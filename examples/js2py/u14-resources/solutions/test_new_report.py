from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from solutions.new_report import new_report


def test_success_and_existing_file_preservation():
    with TemporaryDirectory() as directory:
        path = Path(directory) / "report.txt"
        events = []
        with new_report(path, events) as handle:
            handle.write("ready\n")
        assert handle.closed
        assert path.read_text(encoding="utf-8") == "ready\n"
        assert events == ["acquire-attempt", "acquired", "released"]
        events = []
        with pytest.raises(FileExistsError):
            with new_report(path, events):
                raise AssertionError("body must not execute")
        assert events == ["acquire-attempt"]
        assert path.read_text(encoding="utf-8") == "ready\n"


def test_cleanup_is_not_rollback():
    with TemporaryDirectory() as directory:
        path = Path(directory) / "partial.txt"
        events = []
        with pytest.raises(ValueError, match="body failed"):
            with new_report(path, events) as handle:
                handle.write("partial\n")
                raise ValueError("body failed")
        assert handle.closed
        assert events[-1] == "released"
        assert path.read_text(encoding="utf-8") == "partial\n"
