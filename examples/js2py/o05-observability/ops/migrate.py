from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine

from ops.cluster import checked_root, connect, reject_connection_environment


def upgrade(root: Path, revision: str, database: str = "source"):
    reject_connection_environment()
    checked_root(str(root))
    if database not in {"source", "restored", "damaged"}:
        raise RuntimeError("Refusing migration outside owned laboratory")
    # Every DBAPI connection uses the same environment guard and private passfile.
    engine = create_engine("postgresql+psycopg://", creator=lambda: connect(root, database),
                           hide_parameters=True)
    try:
        with engine.begin() as connection:
            # Serial operator step: app workers NEVER run migrations on startup.
            connection.exec_driver_sql("SET LOCAL lock_timeout = '1s'")
            config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
            config.attributes["connection"] = connection
            command.upgrade(config, revision)
    finally:
        engine.dispose()
