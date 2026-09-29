import pytest


def test_crud(client):
    created = client.post("/tasks", json={"title": "Read", "minutes": 30, "note": "keep"})
    assert created.status_code == 201
    task = created.json()
    assert set(task) == {"id", "title", "minutes", "done", "note"}
    assert type(task["id"]) is int
    assert task["done"] is False
    path = f"/tasks/{task['id']}"
    assert client.get(path).json() == task
    changed = client.patch(path, json={"done": True})
    assert changed.status_code == 200
    assert changed.json() == {**task, "done": True}
    assert client.get(path).json() == changed.json()
    deleted = client.delete(path)
    assert deleted.status_code == 204
    assert deleted.content == b""
    missing = client.get(path)
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Task not found"}


@pytest.mark.parametrize("changes, expected", [({}, "keep"), ({"note": "new"}, "new"), ({"note": None}, None)])
def test_patch_note_states(client, changes, expected):
    task = client.post("/tasks", json={"title": "Read", "minutes": 0, "note": "keep"}).json()
    response = client.patch(f"/tasks/{task['id']}", json=changes)
    assert response.status_code == 200
    expected_task = {**task, "note": expected}
    assert response.json() == expected_task
    stored = client.get(f"/tasks/{task['id']}")
    assert stored.status_code == 200
    assert stored.json() == expected_task


@pytest.mark.parametrize("field, value", [
    ("minutes", True), ("minutes", "3"), ("minutes", 3.0), ("minutes", -1),
    ("title", "   "), ("title", ""), ("title", "x" * 121),
    ("done", "false"), ("done", 0), ("done", None),
    ("note", 3), ("note", "x" * 1001), ("id", 17),
])
def test_invalid_creation_does_not_write(client, field, value):
    payload = {"title": "Read", "minutes": 3, field: value}
    response = client.post("/tasks", json=payload)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(error["loc"] == ["body", field] for error in errors)
    assert client.get("/tasks").json()["total"] == 0


@pytest.mark.parametrize("field", ["title", "minutes", "done"])
def test_non_nullable_patch_is_rejected_without_change(client, field):
    task = client.post("/tasks", json={"title": "Read", "minutes": 3, "note": "keep"}).json()
    path = f"/tasks/{task['id']}"
    response = client.patch(path, json={field: None, "note": "changed"})
    assert response.status_code == 422
    assert client.get(path).json() == task


@pytest.mark.parametrize("path, location", [
    ("/tasks?limit=0", ["query", "limit"]),
    ("/tasks?limit=101", ["query", "limit"]),
    ("/tasks?offset=-1", ["query", "offset"]),
    ("/tasks?offset=bad", ["query", "offset"]),
    ("/tasks/0", ["path", "task_id"]),
    ("/tasks/not-an-id", ["path", "task_id"]),
])
def test_bad_url_inputs(client, path, location):
    response = client.get(path)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == location


def test_pagination(client):
    for title in ["One", "Two", "Three"]:
        assert client.post("/tasks", json={"title": title, "minutes": 0}).status_code == 201
    page = client.get("/tasks", params={"limit": 1, "offset": 1})
    assert page.status_code == 200
    assert page.json() == {
        "items": [{"id": 2, "title": "Two", "minutes": 0, "done": False, "note": None}],
        "limit": 1, "offset": 1, "total": 3,
    }
    assert client.get("/tasks?offset=99").json()["items"] == []


@pytest.mark.parametrize("method, body", [("GET", None), ("PATCH", {"done": True}), ("DELETE", None)])
def test_missing_task(client, method, body):
    response = client.request(method, "/tasks/999", json=body)
    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_malformed_json(client):
    response = client.post("/tasks", content='{"title":', headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "json_invalid"


@pytest.mark.parametrize("unused", [1, 2])
def test_each_case_starts_empty(client, unused):
    assert client.get("/tasks").json()["total"] == 0
    task = client.post("/tasks", json={"title": "Only mine", "minutes": 0}).json()
    assert task["id"] == 1
