from db import session_factory
from safety import fresh_database
from services import create_project, create_task, seed_user
from solutions.project_totals import done_minutes
from testing import migrated_engine


def test_totals_keep_empty_projects_and_exclude_other_statuses():
    with fresh_database() as url, migrated_engine(url) as engine:
        sessions = session_factory(engine)
        with sessions.begin() as session:
            user = seed_user(session)
            empty = create_project(session, "Empty", user)["id"]
            active = create_project(session, "Active", user)["id"]
            outside = create_project(session, "Outside", user)["id"]
            for p, status, minutes in [(active, "done", 20), (active, "done", 10),
                                       (active, "todo", 99), (outside, "done", 500)]:
                create_task(session, p, title="Work", created_by=user, status=status, minutes=minutes)
        with sessions() as session:
            assert done_minutes(session, [empty, active]) == {empty: 0, active: 30}
            assert done_minutes(session, []) == {}
        assert engine.pool.checkedout() == 0
