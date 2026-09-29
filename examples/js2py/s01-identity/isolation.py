"""The lab accepts only its explicit DB URL, never implicit libpq environment."""
import os


def clear_libpq_environment() -> None:
    # Run at process/fixture setup, before connections or worker threads exist.
    # This changes only the current process, never the user's parent shell.
    for name in tuple(os.environ):
        if name.upper().startswith("PG"):
            os.environ.pop(name, None)


def tool_environment() -> dict[str, str]:
    return {name: value for name, value in os.environ.items()
            if not name.upper().startswith("PG")}
