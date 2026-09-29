"""Independent contract tests: run explicitly after attempting the exercise."""
import pytest
from fastapi.testclient import TestClient

from task_api.config import Settings
from task_api.main import create_app


@pytest.fixture
def client():
    with TestClient(create_app(Settings("Independent tests"))) as opened:
        yield opened


def test_pagination_after_gap_and_new_id(client):
    ids = []
    for title in ["A", "B", "C"]:
        result = client.post("/tasks", json={"title": title, "minutes": 0})
        assert result.status_code == 201
        ids.append(result.json()["id"])
    removed = client.delete(f"/tasks/{ids[1]}")
    assert removed.status_code == 204
    assert removed.content == b""
    created = client.post("/tasks", json={"title": "D", "minutes": 0})
    assert created.status_code == 201
    assert created.json()["id"] > max(ids)
    page = client.get("/tasks?limit=1&offset=1")
    assert page.status_code == 200
    assert page.json() == {
        "items": [{"id": ids[2], "title": "C", "minutes": 0, "done": False, "note": None}],
        "limit": 1, "offset": 1, "total": 3,
    }
    assert client.get(f"/tasks/{ids[1]}").status_code == 404


def test_mixed_invalid_patch_is_atomic(client):
    original = client.post("/tasks", json={"title": "Keep", "minutes": 5, "note": "keep"}).json()
    path = f"/tasks/{original['id']}"
    rejected = client.patch(path, json={"title": "Changed", "minutes": True, "note": None})
    assert rejected.status_code == 422
    assert client.get(path).json() == original


def test_empty_patch_preserves_non_default_values(client):
    original = client.post("/tasks", json={"title": "Keep", "minutes": 5, "done": True, "note": "keep"}).json()
    response = client.patch(f"/tasks/{original['id']}", json={})
    assert response.status_code == 200
    assert response.json() == original
    stored = client.get(f"/tasks/{original['id']}")
    assert stored.status_code == 200
    assert stored.json() == original
