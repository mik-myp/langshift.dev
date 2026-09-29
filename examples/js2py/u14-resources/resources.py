from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TextIO


class TextFile:
    def __init__(self, path: Path, events: list[str]) -> None:
        self.path = path
        self.events = events
        self.handle: TextIO | None = None

    def __enter__(self) -> TextIO:
        self.events.append("acquire-attempt")
        self.handle = self.path.open(encoding="utf-8")
        self.events.append("acquired")
        return self.handle

    def __exit__(self, exc_type, exc_value, traceback):
        # A successful __enter__ is the prerequisite for this exit call.
        if self.handle is not None:
            self.handle.close()
        self.events.append("released")
        return False  # Do not suppress a body exception.


@contextmanager
def opened_text(path: Path, events: list[str]) -> Iterator[TextIO]:
    events.append("acquire-attempt")
    handle = path.open(encoding="utf-8")
    events.append("acquired")
    try:
        yield handle
    finally:
        handle.close()
        events.append("released")
