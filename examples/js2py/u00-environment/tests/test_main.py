import subprocess
import sys
from pathlib import Path

import pytest

from main import build_report

PROJECT_DIR = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("tasks", "expected"),
    [
        ([], "Tasks: 0 | Done: 0 | Pending: 0"),
        ([{"done": True}], "Tasks: 1 | Done: 1 | Pending: 0"),
        ([{"done": False}], "Tasks: 1 | Done: 0 | Pending: 1"),
        (
            [{"done": True}, {"done": False}, {"done": False}],
            "Tasks: 3 | Done: 1 | Pending: 2",
        ),
    ],
)
def test_report(tasks, expected):
    assert build_report(tasks) == expected


def test_script_finds_data_from_another_working_directory(tmp_path):
    result = subprocess.run(
        [sys.executable, str(PROJECT_DIR / "main.py")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "Tasks: 3 | Done: 1 | Pending: 2"
    assert result.stderr == ""


def test_import_does_not_run_the_program():
    result = subprocess.run(
        [sys.executable, "-c", "import main"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout == ""
    assert result.stderr == ""
