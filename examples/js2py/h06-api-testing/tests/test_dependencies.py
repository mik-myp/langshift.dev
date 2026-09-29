import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from task_api.config import Settings
from task_api.dependencies import get_settings, get_store
from task_api.main import create_app
from task_api.models import TaskCreate
from task_api.store import MemoryStore


def test_override_store(client, app, overrides):
    fake = MemoryStore()
    fake.create(TaskCreate(title="Only in replacement", minutes=5))

    def replacement_store():
        return fake

    overrides[get_store] = replacement_store
    page = client.get("/tasks").json()
    assert page["items"][0]["title"] == "Only in replacement"
    assert app.state.store.ordered() == []  # The original dependency was bypassed.


def test_dependency_rejection(client, overrides):
    def unavailable_store():
        raise HTTPException(status_code=503, detail="Store unavailable in this test")

    overrides[get_store] = unavailable_store
    response = client.get("/tasks")
    assert response.status_code == 503
    assert response.json() == {"detail": "Store unavailable in this test"}


def test_settings_override(client, overrides):
    def small_page_settings():
        return Settings(app_name="Small test", max_page_size=20)

    overrides[get_settings] = small_page_settings
    response = client.get("/tasks?limit=21")
    assert response.status_code == 422
    assert response.json() == {"detail": "limit exceeds TASKS_MAX_PAGE_SIZE"}
    assert client.get("/tasks?limit=20").status_code == 200


def test_real_trace_cached_and_closed(client, capsys):
    response = client.post("/tasks", json={"title": "Read", "minutes": 0})
    assert response.status_code == 201
    lines = capsys.readouterr().out.splitlines()
    assert lines == [
        "TRACE acquire POST /tasks",
        "TRACE use POST /tasks get_store",
        "TRACE use POST /tasks create_task",
        "TRACE release POST /tasks closed=True",
    ]


def test_real_trace_closed_on_404(client, capsys):
    assert client.get("/tasks/999").status_code == 404
    assert capsys.readouterr().out.splitlines()[-1] == "TRACE release GET /tasks/999 closed=True"


def test_unhandled_errors_raise_by_default(app, overrides):
    def bug():
        raise RuntimeError("deliberate test bug")

    overrides[get_store] = bug
    with TestClient(app) as client:
        with pytest.raises(RuntimeError, match="deliberate test bug"):
            client.get("/tasks")
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/tasks")
        assert response.status_code == 500
        assert response.text == "Internal Server Error"


def test_two_apps_do_not_share_store():
    first = create_app(Settings("First"))
    second = create_app(Settings("Second"))
    with TestClient(first) as left, TestClient(second) as right:
        left.post("/tasks", json={"title": "Only left", "minutes": 0})
        assert left.get("/tasks").json()["total"] == 1
        assert right.get("/tasks").json()["total"] == 0
