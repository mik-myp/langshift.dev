"""Application adapter: _FILE is implemented here, not automatically by Compose."""
import os
from pathlib import Path


def database_url():
    value = os.environ.get("DATABASE_URL")
    filename = os.environ.get("DATABASE_URL_FILE")
    if bool(value) == bool(filename):
        raise ValueError("Configure exactly one database connection source")
    if filename:
        try:
            value = Path(filename).read_text(encoding="utf-8").strip()
        except (OSError, UnicodeError):
            raise ValueError("Database credential file cannot be read") from None
    if not value or not value.startswith("postgresql+psycopg://"):
        raise ValueError("A PostgreSQL psycopg connection is required")
    return value
