import os
from pathlib import Path
from alembic import command
import pytest
from sqlalchemy import inspect, text
from db import make_engine
from history_data import insert_old_task, snapshot
from migrate import configuration, upgrade
from safety import fresh_database


def test_archive_extension_preserves_old_rows_and_refuses_loss():
    with fresh_database() as url:
        engine = make_engine(url)
        try:
            upgrade(url)
            with engine.begin() as connection:
                insert_old_task(connection)
                before = snapshot(connection)
            config = configuration(url)
            root = Path(__file__).resolve().parents[1]
            config.set_main_option("version_locations", os.pathsep.join([
                str(root / "migrations/versions"), str(root / "solutions/versions")]))
            command.upgrade(config, "004_archived_at")
            assert "archived_at" in {c["name"] for c in inspect(engine).get_columns("projects")}
            with engine.begin() as connection:
                assert snapshot(connection) == before
                assert connection.scalar(text("SELECT archived_at FROM projects")) is None
                connection.execute(text("UPDATE projects SET archived_at=CURRENT_TIMESTAMP"))
            with pytest.raises(RuntimeError, match="archive history"):
                command.downgrade(config, "003_contract")
            with engine.connect() as connection:
                assert connection.scalar(text("SELECT archived_at IS NOT NULL FROM projects")) is True
                assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "004_archived_at"
        finally:
            engine.dispose()
