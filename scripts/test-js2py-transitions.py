#!/usr/bin/env python3
"""Maintainer-only CPython/uv integration: L11–L14, not new learner prerequisites."""

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROWS = json.loads(
    (ROOT / "scripts/tests/fixtures/js2py-transition-foundations.json").read_text()
)
OUTPUTS = {
    "u11-typing": "[30, 0, 15]\n{'count': 3, 'minutes': 45}\n[30, 0, 90, 15]\n",
    "u12-models": "45\nTrue False\n15\n! Write\nTrue False\n['python'] []\n",
    "u13-decorators": "['cost']\n11 11\ncost\nTrue\n",
    "u14-resources": "[]\n30\n['started', 'yield 30']\n['started', 'yield 30', 'finished']\nalpha\nTrue ['acquire-attempt', 'acquired', 'released']\nTrue ['acquire-attempt', 'acquired', 'released']\nalpha\n",
}
COUNTS = {
    "u11-typing": (8, 2),
    "u12-models": (9, 2),
    "u13-decorators": (8, 7),
    "u14-resources": (12, 2),
}


def environment():
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("PYTHON")
    }
    for key in ["VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT", "UV_ACTIVE", "UV_PYTHON"]:
        env.pop(key, None)
    env.update(PYTHONIOENCODING="utf-8", PYTHONNOUSERSITE="1", UV_NO_CONFIG="1")
    return env


def run(directory, *command, expected=0, contains=None):
    result = subprocess.run(
        command,
        cwd=directory,
        env=environment(),
        text=True,
        capture_output=True,
        timeout=180,
    )
    if result.returncode != expected:
        raise AssertionError(
            (command, expected, result.returncode, result.stdout, result.stderr)
        )
    if contains is not None and contains not in result.stdout + result.stderr:
        raise AssertionError((command, contains, result.stdout, result.stderr))
    return result.stdout


def py(directory, *command, **kwargs):
    return run(directory, "uv", "run", "--locked", "python", *command, **kwargs)


def mutation(directory, filename, before, after, suite="tests"):
    target = directory / filename
    original = target.read_text()
    assert original.count(before) >= 1, (filename, before)
    target.write_text(original.replace(before, after, 1))
    try:
        # Fresh process and no stale bytecode for same-size edits.
        for cache in directory.rglob("__pycache__"):
            if ".venv" not in cache.parts:
                shutil.rmtree(cache)
        py(directory, "-m", "pytest", "-q", suite, expected=1, contains="failed")
    finally:
        target.write_text(original)
        for cache in directory.rglob("__pycache__"):
            if ".venv" not in cache.parts:
                shutil.rmtree(cache)


def check_row(row):
    name = row["lab"]
    archive_path = ROOT / "public/learning-assets/js2py" / (name + ".zip")
    with tempfile.TemporaryDirectory(prefix="js2py-transitions-") as directory:
        destination = Path(directory)
        with zipfile.ZipFile(archive_path) as archive:
            assert all(
                not Path(n).is_absolute() and ".." not in Path(n).parts
                for n in archive.namelist()
            )
            archive.extractall(destination)
        lab = destination / name
        assert not (lab / ".venv").exists()
        run(lab, "uv", "sync", "--locked")
        assert (
            py(lab, "-c", "import platform; print(platform.python_version())").strip()
            == "3.13.15"
        )
        assert py(lab, "app.py") == OUTPUTS[name]
        main, extra = COUNTS[name]
        py(lab, "-m", "pytest", "-q", contains=f"{main} passed")
        py(lab, "-m", "pytest", "-q", "solutions", contains=f"{extra} passed")
        # The annotated declaration smoke scope is explicit and has no server/file effects.
        page = (ROOT / "content/docs/js2py" / (row["slug"] + ".mdx")).read_text()
        for code in re.findall(r"^```python[^\n]*\n(.*?)^```", page, re.M | re.S):
            py(lab, "-I", "-c", code)
        if name == "u11-typing":
            py(lab, "-m", "mypy", contains="Success:")
            py(
                lab,
                "-m",
                "mypy",
                "errors/static_errors.py",
                expected=1,
                contains="Found 3 errors",
            )
            py(
                lab,
                "-m",
                "mypy",
                "errors/annotation_only.py",
                expected=1,
                contains="arg-type",
            )
            assert py(lab, "errors/annotation_only.py") == "33\n"
            py(
                lab,
                "-m",
                "mypy",
                "--config-file",
                "errors/mypy-default.ini",
                "errors/unchecked.py",
                contains="Success:",
            )
            py(
                lab,
                "-m",
                "mypy",
                "--config-file",
                "errors/mypy-default.ini",
                "--check-untyped-defs",
                "errors/unchecked.py",
                expected=1,
                contains="operator",
            )
            py(lab, "errors/unchecked.py", expected=1, contains="TypeError")
            py(lab, "-m", "mypy", "errors/bool_static.py", contains="Success:")
            py(lab, "-m", "errors.bool_static", expected=1, contains="ValueError")
            py(lab, "-m", "errors.bad_json", expected=1, contains="ValueError")
            mutation(
                lab,
                "estimates.py",
                "type(value) is not int",
                "not isinstance(value, int)",
            )
            mutation(
                lab,
                "solutions/first_over.py",
                "    for value in values:\n        non_negative_int(value)\n",
                "",
                "solutions",
            )
        elif name == "u12-models":
            assert py(lab, "errors/shared_state.py") == "['Read']\n"
            py(lab, "errors/missing_self.py", expected=1, contains="TypeError")
            assert py(lab, "-m", "errors.no_validation") == "str\n"
            mutation(lab, "models.py", "self.tasks = list(tasks)", "self.tasks = tasks")
            mutation(
                lab,
                "solutions/work_log.py",
                "self.entries.append(checked_minutes(minutes))",
                "self.entries.append(minutes)",
                "solutions",
            )
        elif name == "u13-decorators":
            assert py(lab, "expansion.py") == "11 11\n"
            assert py(lab, "order.py") == "14\n7 4\n"
            timeline = py(lab, "timing.py")
            assert (
                timeline
                == "['evaluate outer', 'evaluate inner', 'apply inner', 'apply outer']\n['evaluate outer', 'evaluate inner', 'apply inner', 'apply outer', 'call 4', 'call 5']\n"
            )
            py(lab, "errors/missing_return.py", expected=1, contains="TypeError")
            py(
                lab,
                "-m",
                "errors.duplicate",
                expected=1,
                contains="duplicate operation",
            )
            mutation(
                lab, "decorators.py", "return function(value) * 2", "return value * 2"
            )
            mutation(
                lab,
                "solutions/reject_above.py",
                "            if type(value)",
                "            function(value)\n            if type(value)",
                "solutions",
            )
        else:
            assert (
                py(lab, "break_demo.py")
                == "30\n['started', 'yield 30']\n['started', 'yield 30', 'finished']\n"
            )
            assert py(lab, "errors/suppressed.py") == "hidden\ncontinued\n"
            py(lab, "errors/two_yields.py", expected=1, contains="RuntimeError")
            mutation(lab, "resources.py", "return False", "return True")
            mutation(
                lab,
                "solutions/new_report.py",
                'path.open("x",',
                'path.open("w",',
                "solutions",
            )
        py(lab, "-m", "pytest", "-q", contains=f"{main} passed")
        py(lab, "-m", "pytest", "-q", "solutions", contains=f"{extra} passed")
        # A second empty directory reconstruction from the exact same declared files.
        second = destination / "second" / name
        names = json.loads((ROOT / f"examples/js2py/{name}-files.json").read_text())
        for item in names:
            target = second / item
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(lab / item, target)
        run(second, "uv", "sync", "--locked")
        assert py(second, "app.py") == OUTPUTS[name]
        py(second, "-m", "pytest", "-q", contains=f"{main} passed")
        print(
            f"{name}: clean ZIP + second reconstruction, {main}+{extra} tests, intentional failures, two detected mutations PASS",
            flush=True,
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lab", choices=[row["lab"] for row in ROWS])
    args = parser.parse_args()
    for row in ROWS:
        if args.lab is None or args.lab == row["lab"]:
            check_row(row)


if __name__ == "__main__":
    main()
