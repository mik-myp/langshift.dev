from fastapi.testclient import TestClient
import pytest
from sqlalchemy import event, func, select, text
from sqlalchemy.exc import IntegrityError

import api
from commit_failure import demonstrate
from db import make_engine, session_factory
from models import Project, ProjectMember, Task, User
from services import create_project, seed_user
from safety import checked_url


def owner(engine):
    with session_factory(engine).begin() as session:
        return seed_user(session)


def count(engine, model):
    with session_factory(engine)() as session:
        return session.scalar(select(func.count()).select_from(model))


def test_atomic_success(engine):
    user_id = owner(engine)
    with session_factory(engine).begin() as session:
        project = create_project(session, "Study", user_id)
    with session_factory(engine)() as session:
        member = session.get(ProjectMember, (project["id"], user_id))
        assert member.role == "owner"
    assert count(engine, Project) == 1


def test_second_write_failure_leaves_neither_row(engine):
    user_id = owner(engine)
    with pytest.raises(IntegrityError):
        with session_factory(engine).begin() as session:
            create_project(session, "No residue", user_id, owner_role="broken")
    assert count(engine, Project) == count(engine, ProjectMember) == 0
    assert engine.pool.checkedout() == 0


def test_close_without_commit_rolls_back(engine):
    with session_factory(engine)() as session:
        seed_user(session, "not committed")
    assert count(engine, User) == 0


def test_commit_failure_requires_explicit_rollback(engine):
    demonstrate(engine)


def test_api_success_failure_and_pool_return(engine, monkeypatch):
    user_id = owner(engine)
    events = []
    event.listen(engine, "checkout", lambda *args: events.append("out"))
    event.listen(engine, "checkin", lambda *args: events.append("in"))
    real = api.create_project
    with TestClient(api.create_app(engine)) as client:
        def broken(session, name, owner_id):
            return real(session, name, owner_id, owner_role="broken")
        monkeypatch.setattr(api, "create_project", broken)
        response = client.post("/projects", json={"name": "No residue", "owner_id": user_id})
        assert response.status_code == 409
        assert response.json() == {"detail": "Database rule rejected this write"}
        assert count(engine, Project) == count(engine, ProjectMember) == 0
        assert engine.pool.checkedout() == 0
        monkeypatch.setattr(api, "create_project", real)
        response = client.post("/projects", json={"name": "Recovery", "owner_id": user_id})
        assert response.status_code == 201
        assert client.get("/projects").json() == [response.json()]
        assert engine.pool.checkedout() == 0
    assert events.count("out") == events.count("in") > 0


def test_tasks_are_persisted_filtered_and_validated(engine):
    user_id = owner(engine)
    with TestClient(api.create_app(engine)) as client:
        project_id = client.post("/projects", json={"name": "P", "owner_id": user_id}).json()["id"]
        url = f"/projects/{project_id}/tasks"
        for title, status in [("A", "todo"), ("B", "done"), ("C", "todo")]:
            assert client.post(url, json={"title": title, "created_by": user_id, "status": status}).status_code == 201
        assert [t["title"] for t in client.get(url + "?status=todo&limit=1&offset=1").json()] == ["C"]
        assert client.post(url, json={"title": " ", "created_by": user_id}).status_code == 422
        assert client.get(url + "?limit=101").status_code == 422
        assert client.get("/projects/999999/tasks").status_code == 404
    assert count(engine, Task) == 3


def test_committed_data_survives_new_engine(engine, database_url):
    owner(engine)
    other = make_engine(database_url)
    try:
        assert count(other, User) == 1
    finally:
        other.dispose()


def test_failed_flush_blocks_use_until_rollback(engine):
    with session_factory(engine)() as session:
        session.add(User(login=" "))
        with pytest.raises(IntegrityError):
            session.flush()
        from sqlalchemy.exc import PendingRollbackError
        with pytest.raises(PendingRollbackError):
            session.execute(text("SELECT 1"))
        session.rollback()
        assert session.scalar(text("SELECT 1")) == 1


def test_guard_rejects_arbitrary_database():
    with pytest.raises(RuntimeError, match="Refusing"):
        checked_url("postgresql+psycopg://lab_owner@localhost/production")
