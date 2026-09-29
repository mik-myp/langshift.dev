"""Single-writer disposable counter. No transactions, concurrency or fsync promise."""
import argparse
import json
import os
from pathlib import Path

from config import data_directory


def count(directory: Path, increment: bool = False) -> int:
    file = directory / "counter.json"
    value = json.loads(file.read_text())["count"] if file.exists() else 0
    if type(value) is not int or value < 0:
        raise ValueError("invalid disposable counter; do not silently reset it")
    if increment:
        value += 1
        temporary = directory / "counter.pending"
        temporary.write_text(json.dumps({"count": value}) + "\n")
        temporary.replace(file)
    return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--increment", action="store_true")
    args = parser.parse_args()
    print(count(data_directory(os.environ), args.increment))
