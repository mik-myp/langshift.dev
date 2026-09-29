import pytest
from fastapi.testclient import TestClient

from task_api.config import Settings
from task_api.main import create_app


@pytest.fixture
def app():
    # Default fixture scope is function: one new app/store per test case.
    return create_app(Settings(app_name="H06 tests"))


@pytest.fixture
def client(app):
    with TestClient(app) as opened_client:
        yield opened_client


@pytest.fixture
def overrides(app):
    previous = app.dependency_overrides.copy()
    try:
        yield app.dependency_overrides
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)
