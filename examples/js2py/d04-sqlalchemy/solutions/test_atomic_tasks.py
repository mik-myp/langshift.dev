import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from db import make_engine, session_factory
from models import Base, Task
from safety import fresh_database
from services import create_project, create_task, seed_user
from solutions.atomic_tasks import copy_titles


def test_copy_titles_is_one_unit_of_work():
    with fresh_database() as url:
        engine = make_engine(url)
        try:
            Base.metadata.create_all(engine)
            sessions = session_factory(engine)
            with sessions.begin() as session:
                user = seed_user(session)
                project = create_project(session, "Copies", user)
                create_task(session, project["id"], title="Existing", created_by=user)
            with pytest.raises(IntegrityError):
                with sessions.begin() as session:
                    copy_titles(session, project["id"], user, ["Valid", " "])
            with sessions() as session:
                assert session.scalar(select(func.count()).select_from(Task)) == 1
            with sessions.begin() as session:
                result = copy_titles(session, project["id"], user, ["A", "B"])
            assert len(result) == 2
            with sessions() as session:
                assert session.scalar(select(func.count()).select_from(Task)) == 3
            assert engine.pool.checkedout() == 0
        finally:
            engine.dispose()
