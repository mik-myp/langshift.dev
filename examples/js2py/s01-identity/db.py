import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from isolation import clear_libpq_environment

clear_libpq_environment()


def database_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url.startswith("postgresql+psycopg://"):
        # Never include an actual URL or configuration contents in this error.
        raise RuntimeError("DATABASE_URL must identify the owned PostgreSQL lab")
    return url


def bounded_seconds(name: str, default: int, lower: int, upper: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except ValueError:
        raise RuntimeError(f"{name} must be an integer") from None
    if not lower <= value <= upper:
        raise RuntimeError(f"{name} is outside the documented range")
    return value


engine = create_engine(database_url(), echo=False, hide_parameters=True,
                       pool_pre_ping=True, pool_size=5, max_overflow=5, isolation_level="READ COMMITTED")
SessionLocal = sessionmaker(engine, expire_on_commit=False)
SESSION_TTL = bounded_seconds("SESSION_TTL_SECONDS", 900, 60, 3600)
EXPECTED_REVISION = "004_identity"
