"""A real COMMIT failure, not merely a flush failure mislabeled as commit."""
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from db import make_engine, session_factory


def demonstrate(engine):
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE commit_probe (value integer, "
                                "CONSTRAINT commit_probe_unique UNIQUE(value) "
                                "DEFERRABLE INITIALLY DEFERRED)"))
    with session_factory(engine)() as session:
        session.execute(text("INSERT INTO commit_probe VALUES (7), (7)"))
        print("two INSERT values accepted; deferred check awaits COMMIT")
        try:
            session.commit()
        except IntegrityError:
            print("COMMIT failed")
        else:
            raise AssertionError("expected the deferred unique constraint to fail")
        try:
            session.execute(text("SELECT 1"))
        except InvalidRequestError:
            print("Session refuses reuse before rollback")
        else:
            raise AssertionError("expected failed Session state")
        session.rollback()
        assert session.scalar(text("SELECT count(*) FROM commit_probe")) == 0
        session.execute(text("INSERT INTO commit_probe VALUES (8)"))
        session.commit()
    with engine.connect() as connection:
        assert connection.execute(text("SELECT value FROM commit_probe")).scalars().all() == [8]
    print("rollback restored Session; next transaction committed one row")
    print("checked out:", engine.pool.checkedout())


def main():
    engine = make_engine()
    try:
        demonstrate(engine)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
