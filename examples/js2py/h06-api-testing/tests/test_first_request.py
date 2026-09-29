from fastapi.testclient import TestClient

from task_api.config import Settings
from task_api.main import create_app


def test_create_without_fixtures():
    app = create_app(Settings(app_name="First test"))
    with TestClient(app) as client:
        response = client.post("/tasks", json={"title": "  Read  ", "minutes": 30})
    assert response.status_code == 201
    assert response.json() == {
        "id": 1, "title": "  Read  ", "minutes": 30, "done": False, "note": None,
    }
