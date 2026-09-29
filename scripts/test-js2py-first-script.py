#!/usr/bin/env python3
"""Run the exact introductory commands and maintainer checks on Python 3.13."""

import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UV = ["uv", "run", "--no-project", "--python", "3.13", "python"]


def run(arguments, cwd):
    result = subprocess.run(
        arguments, cwd=cwd, capture_output=True, text=True, timeout=120
    )
    if result.returncode:
        raise RuntimeError(f"Failed: {arguments}\n{result.stdout}\n{result.stderr}")
    return result.stdout


def main():
    if not shutil.which("uv"):
        raise SystemExit("This maintainer integration check needs uv and Python 3.13.")
    with tempfile.TemporaryDirectory(prefix="js2py-first-script-") as directory:
        parent = Path(directory)
        # A containing project must not become the beginner script's environment.
        (parent / "pyproject.toml").write_text(
            '[project]\nname = "must-not-be-used"\nversion = "0.0.0"\nrequires-python = ">=99"\n'
        )
        (parent / "uv.lock").write_text("deliberately invalid parent lock\n")
        # The repository builds this trusted archive from an explicit allowlist.
        with zipfile.ZipFile(
            ROOT / "public/learning-assets/js2py/u00-first-script.zip"
        ) as archive:
            archive.extractall(parent)
        lab = parent / "u00-first-script"
        original_paths = sorted(str(p.relative_to(parent)) for p in parent.rglob("*"))
        version = run(UV + ["--version"], lab).strip()
        assert version.startswith("Python 3.13."), version
        assert run(UV + ["first_steps.py"], lab) == "Hello!\nPython\n"
        assert (
            run(UV + ["solutions/about_me.py"], lab)
            == "My next skill:\nPython\nFastAPI\n"
        )
        assert original_paths == sorted(
            str(p.relative_to(parent)) for p in parent.rglob("*")
        )
        print(
            f"Downloaded first script: {version}; no project files created; parent project ignored"
        )

        scratch = parent / "from-empty-folder"
        scratch.mkdir()
        (scratch / "first_steps.py").write_text(
            'course = "Python"\nprint("Hello!")\nprint(course)\n'
        )
        assert run(UV + ["first_steps.py"], scratch) == "Hello!\nPython\n"
        (scratch / "about_me.py").write_bytes(
            (lab / "solutions/about_me.py").read_bytes()
        )
        assert run(UV + ["about_me.py"], scratch) == "My next skill:\nPython\nFastAPI\n"
        print("Empty-folder path and the learner's independent exercise command PASS")

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
                "test_js2py_first_script.py",
                "-v",
            ],
            cwd=ROOT,
            env=env,
            check=True,
            timeout=120,
        )
        manifest = json.loads(
            (ROOT / "examples/js2py/u00-first-script-files.json").read_text()
        )
        assert "pyproject.toml" not in manifest


if __name__ == "__main__":
    main()
