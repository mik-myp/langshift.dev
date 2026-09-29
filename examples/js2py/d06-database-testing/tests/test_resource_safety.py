import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from safety import checked_url, connect_admin, fresh_database
from testing import migrated_engine


def test_guard_refuses_developer_and_production_urls():
    for url in ["sqlite://", "postgresql+psycopg://lab_owner@localhost/dev",
                "postgresql+psycopg://lab_owner@/postgres"]:
        with pytest.raises(RuntimeError, match="Refusing"):
            checked_url(url)


def test_fixture_setup_failure_still_disposes_and_drops_database():
    name = None
    pool_events = []
    def bad_prepare(engine):
        from sqlalchemy import event
        event.listen(engine, "close", lambda *args: pool_events.append("closed"))
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE setup_probe (n integer CHECK (n>0))"))
            connection.execute(text("INSERT INTO setup_probe VALUES (-1)"))
    with pytest.raises(IntegrityError):
        with fresh_database() as url:
            name = checked_url(url).database
            with migrated_engine(url, prepare=bad_prepare):
                raise AssertionError("setup should never reach yield")
    assert pool_events == ["closed"]
    with connect_admin(checked_url()) as connection:
        assert connection.execute("SELECT count(*) FROM pg_database WHERE datname=%s", (name,)).fetchone()[0] == 0


def test_exception_in_test_body_still_cleans_resources():
    with pytest.raises(ValueError, match="body failed"):
        with fresh_database() as url:
            name = checked_url(url).database
            with migrated_engine(url) as engine:
                with engine.connect() as connection:
                    assert connection.scalar(text("SELECT 1")) == 1
                raise ValueError("body failed")
    with connect_admin(checked_url()) as connection:
        assert connection.execute("SELECT count(*) FROM pg_database WHERE datname=%s", (name,)).fetchone()[0] == 0
