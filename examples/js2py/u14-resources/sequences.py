from collections.abc import Generator
from pathlib import Path


def tracked_minutes(values: list[int], events: list[str]) -> Generator[int]:
    events.append("started")
    try:
        for value in values:
            if type(value) is not int or value < 0:
                raise ValueError("minutes must be a non-negative integer")
            events.append("yield " + str(value))
            yield value
    finally:
        events.append("finished")


def lines_from(path: Path) -> Generator[str]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            yield line.rstrip("\n")
