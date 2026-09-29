#!/usr/bin/env python3
"""Run L02's documented commands from a download and an empty folder on 3.13."""

import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UV = ["uv", "run", "--no-project", "--python", "3.13", "python"]


def run(arguments, cwd, expected_error=None):
    result = subprocess.run(
        arguments, cwd=cwd, capture_output=True, text=True, timeout=120
    )
    if expected_error:
        assert result.returncode != 0, arguments
        assert result.stderr.splitlines()[-1].startswith(expected_error + ":"), (
            result.stderr
        )
    elif result.returncode:
        raise RuntimeError(f"Failed: {arguments}\n{result.stdout}\n{result.stderr}")
    return result.stdout


def main():
    if not shutil.which("uv"):
        raise SystemExit("This maintainer integration check needs uv and Python 3.13.")
    cases = json.loads(
        (ROOT / "scripts/tests/fixtures/js2py-containers.json").read_text()
    )
    with tempfile.TemporaryDirectory(prefix="js2py-containers-") as directory:
        parent = Path(directory)
        (parent / "pyproject.toml").write_text(
            '[project]\nname = "must-not-be-used"\nversion = "0.0.0"\nrequires-python = ">=99"\n'
        )
        (parent / "uv.lock").write_text("deliberately invalid parent lock\n")
        # Trusted repository artifact built from a checked allowlist, not user uploads.
        with zipfile.ZipFile(
            ROOT / "public/learning-assets/js2py/u02-containers.zip"
        ) as archive:
            archive.extractall(parent)
        lab = parent / "u02-containers"
        before = sorted(str(p.relative_to(parent)) for p in parent.rglob("*"))
        parent_files = {
            name: (parent / name).read_bytes() for name in ("pyproject.toml", "uv.lock")
        }
        version = run(UV + ["--version"], lab).strip()
        assert version.startswith("Python 3.13."), version
        for filename, expected in cases["files"].items():
            assert (
                run(UV + [filename], lab, expected.get("error")) == expected["stdout"]
            ), filename
        assert before == sorted(str(p.relative_to(parent)) for p in parent.rglob("*"))
        assert all(
            (parent / name).read_bytes() == data for name, data in parent_files.items()
        )
        print(
            f"Downloaded L02: {version}; 18 scripts verified, including 5 intentional errors"
        )
        print("Incompatible parent project ignored; no project files created")

        scratch = parent / "from-empty-folder"
        scratch.mkdir()
        (scratch / "study_board.py").write_bytes(
            (lab / "solutions/study_board.py").read_bytes()
        )
        assert (
            run(UV + ["study_board.py"], scratch)
            == cases["files"]["solutions/study_board.py"]["stdout"]
        )
        code = (
            (scratch / "study_board.py")
            .read_text()
            .replace('["minutes"] = 35', '["minutes"] = 50')
        )
        (scratch / "study_board.py").write_text(code)
        assert run(UV + ["study_board.py"], scratch) == (
            cases["files"]["solutions/study_board.py"]["stdout"].replace(
                "55 minutes", "70 minutes"
            )
        )
        print("Empty-folder command and input variation PASS")

        interpreter = run(UV + ["-c", "import sys; print(sys.executable)"], lab).strip()
        env = dict(os.environ, JS2PY_PYTHON=interpreter)
        subprocess.run(
            [
                interpreter,
                "-m",
                "unittest",
                "discover",
                "-s",
                "scripts/tests",
                "-p",
                "test_js2py_containers.py",
                "-v",
            ],
            cwd=ROOT,
            env=env,
            check=True,
            timeout=120,
        )


if __name__ == "__main__":
    main()
