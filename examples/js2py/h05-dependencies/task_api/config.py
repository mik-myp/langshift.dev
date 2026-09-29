import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str
    max_page_size: int = 100


def load_settings(environ: dict[str, str] | None = None) -> Settings:
    source = os.environ if environ is None else environ
    name = source.get("TASKS_APP_NAME", "").strip()
    if not name:
        raise ValueError("TASKS_APP_NAME is required and must not be blank")
    raw_limit = source.get("TASKS_MAX_PAGE_SIZE", "100")
    # Environment values are strings, not already validated Python integers.
    if not raw_limit.isascii() or not raw_limit.isdecimal():
        raise ValueError("TASKS_MAX_PAGE_SIZE must be an integer from 20 to 100")
    try:
        limit = int(raw_limit)
    except ValueError:
        raise ValueError("TASKS_MAX_PAGE_SIZE must be an integer from 20 to 100") from None
    if not 20 <= limit <= 100:
        raise ValueError("TASKS_MAX_PAGE_SIZE must be an integer from 20 to 100")
    return Settings(app_name=name, max_page_size=limit)
