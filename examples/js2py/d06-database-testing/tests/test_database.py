import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from commit_failure import demonstrate
from db import session_factory
from history_data import insert_old_task
from models import Project, ProjectMember, Task, User
from query_plan import experiment
from services import create_project, create_task, list_tasks, seed_user


def seed(engine):
    with session_factory(engine).begin() as session:
        user = seed_user(session)
        project = create_project(session, "Study", user)
        return user, project["id"]


def test_actual_postgresql_18_and_non_superuser(engine):
    with engine.connect() as connection:
        assert 180000 <= int(connection.scalar(text("SHOW server_version_num"))) < 190000
        assert connection.scalar(text("SELECT current_database()" )).startswith("js2py_lab_")
        assert connection.scalar(text("SELECT rolsuper FROM pg_roles WHERE rolname=current_user")) is False
        assert connection.scalar(text("SELECT inet_server_addr()")) is None  # Unix socket


@pytest.mark.parametrize("change", [
    "status='bogus'", "minutes=-1", "title=' '", "created_by=999999999",
    "project_id=999999999", "priority=3", "priority=NULL",
])
def test_database_constraints_even_without_api_validation(engine, change):
    with engine.begin() as connection:
        insert_old_task(connection)
    # These are fixed test SQL literals, never untrusted request fragments.
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(text("UPDATE tasks SET " + change))
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM tasks WHERE status='done' AND minutes=30 AND priority=0")) == 1
    assert engine.pool.checkedout() == 0


def test_duplicate_login_and_membership(engine):
    user, project = seed(engine)
    sessions = session_factory(engine)
    for row in [User(login="alice"), ProjectMember(project_id=project, user_id=user, role="member")]:
        with pytest.raises(IntegrityError):
            with sessions.begin() as session:
                session.add(row)
    with sessions() as session:
        assert session.get(ProjectMember, (project, user)).role == "owner"


def test_second_write_atomic_rollback_then_success(engine):
    with session_factory(engine).begin() as session:
        user = seed_user(session)
    with pytest.raises(IntegrityError):
        with session_factory(engine).begin() as session:
            create_project(session, "Fail", user, owner_role="broken")
    with session_factory(engine)() as session:
        assert session.scalar(select(func.count()).select_from(Project)) == 0
        assert session.scalar(select(func.count()).select_from(ProjectMember)) == 0
    with session_factory(engine).begin() as session:
        create_project(session, "Next request", user)
    assert engine.pool.checkedout() == 0


def test_commit_time_failure_and_session_recovery(engine):
    demonstrate(engine)


def test_query_scope_filter_and_stable_pagination(engine):
    user, project = seed(engine)
    sessions = session_factory(engine)
    with sessions.begin() as session:
        other = create_project(session, "Other", user)["id"]
        create_task(session, other, title="Do not leak", created_by=user)
        for title, status in [("A", "todo"), ("B", "done"), ("C", "todo"), ("D", "todo")]:
            create_task(session, project, title=title, created_by=user, status=status)
    with sessions() as session:
        assert [row["title"] for row in list_tasks(session, project, "todo", 2, 0)] == ["A", "C"]
        assert [row["title"] for row in list_tasks(session, project, "todo", 2, 2)] == ["D"]
        assert list_tasks(session, project, "doing") == []
        assert len(list_tasks(session, project, None, 100)) == 4


def test_restrict_delete_preserves_children(engine):
    user, project = seed(engine)
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM projects WHERE id=:p"), {"p": project})
    with session_factory(engine)() as session:
        assert session.get(ProjectMember, (project, user)) is not None


def test_real_query_plan_and_index(engine):
    report = experiment(engine)
    assert report["rows_seeded"] == 60000
    # Plans/cost/timing vary by version, data distribution and machine.
    assert report["returned"] == 20
