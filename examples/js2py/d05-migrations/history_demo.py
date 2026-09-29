from alembic import command
from sqlalchemy import text
from db import make_engine
from history_data import insert_old_task, snapshot
from migrate import configuration, upgrade


def main():
    upgrade(revision="001_base")
    engine = make_engine()
    try:
        with engine.begin() as connection:
            user, project, task = insert_old_task(connection)
        upgrade(revision="002_expand")
        with engine.begin() as connection:
            insert_old_task(connection, "Old app still writes", user_id=user, project_id=project)
            before = snapshot(connection)
            connection.execute(text("UPDATE tasks SET priority = 2 WHERE id = :id"), {"id": task})
        upgrade()
        with engine.connect() as connection:
            assert snapshot(connection) == before
            priorities = list(connection.execute(text("SELECT priority FROM tasks ORDER BY id")).scalars())
            print("preserved rows:", len(before))
            print("priorities:", priorities)
            print("revision:", connection.scalar(text("SELECT version_num FROM alembic_version")))
        command.check(configuration())
        print("metadata drift: none detected")
        try:
            command.downgrade(configuration(), "001_base")
        except RuntimeError as error:
            print("downgrade refused:", str(error))
        with engine.connect() as connection:
            assert snapshot(connection) == before
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "003_contract"
        print("refused downgrade left revision and data unchanged")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
