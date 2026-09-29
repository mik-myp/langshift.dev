#!/usr/bin/env python3
"""Run L04's documented download and empty-folder commands on Python 3.13."""

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
        (ROOT / "scripts/tests/fixtures/js2py-functions.json").read_text()
    )
    with tempfile.TemporaryDirectory(prefix="js2py-functions-") as directory:
        parent = Path(directory)
        (parent / "pyproject.toml").write_text(
            '[project]\nname = "must-not-be-used"\nversion = "0.0.0"\nrequires-python = ">=99"\n'
        )
        (parent / "uv.lock").write_text("deliberately invalid parent lock\n")
        # Trusted repository artifact built from a checked allowlist, not user uploads.
        with zipfile.ZipFile(
            ROOT / "public/learning-assets/js2py/u04-functions.zip"
        ) as archive:
            archive.extractall(parent)
        lab = parent / "u04-functions"
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
            f"Downloaded L04: {version}; 23 scripts verified, including 8 expected errors"
        )
        print("Incompatible parent project ignored; no project files created")

        scratch = parent / "from-empty-folder"
        scratch.mkdir()
        learner = scratch / "study_rules.py"
        learner.write_bytes((lab / "solutions/study_rules.py").read_bytes())
        assert (
            run(UV + [learner.name], scratch)
            == cases["files"]["solutions/study_rules.py"]["stdout"]
        )
        code = learner.read_text()
        assert code.count("small_budget = 20") == 1
        learner.write_text(code.replace("small_budget = 20", "small_budget = 0"))
        expected = cases["files"]["solutions/study_rules.py"]["stdout"].replace(
            "Within 20: ['Read', 'Zero']", "Within 0: ['Zero']"
        )
        assert run(UV + [learner.name], scratch) == expected
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
                "test_js2py_functions.py",
                "-v",
            ],
            cwd=ROOT,
            env=env,
            check=True,
            timeout=120,
        )


if __name__ == "__main__":
    main()
