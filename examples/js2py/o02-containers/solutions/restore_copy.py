"""A disposable-file exercise, NOT a live database backup procedure."""
from pathlib import Path
import shutil

from volume_probe import count


def restore_counter(source: Path, empty_destination: Path) -> int:
    count(source)  # Refuse corrupt data before copying.
    if any(empty_destination.iterdir()):
        raise ValueError("restore destination must be empty")
    shutil.copyfile(source / "counter.json", empty_destination / "counter.json")
    return count(empty_destination)
