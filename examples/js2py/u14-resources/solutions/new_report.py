from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TextIO


@contextmanager
def new_report(path: Path, events: list[str]) -> Iterator[TextIO]:
    events.append("acquire-attempt")
    handle = path.open("x", encoding="utf-8")
    events.append("acquired")
    try:
        yield handle
    finally:
        handle.close()
        events.append("released")
