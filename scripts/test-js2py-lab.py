#!/usr/bin/env python3
"""Verify the actual download, unfinished exercise, answer, and clean-room guide."""

import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "examples/js2py/u00-environment"


def run(arguments, cwd, *, expect_failure=False):
    result = subprocess.run(
        arguments, cwd=cwd, text=True, capture_output=True, timeout=120
    )
    output = result.stdout + result.stderr
    if (result.returncode != 0) != expect_failure:
        raise RuntimeError(
            f"Unexpected exit {result.returncode}: {arguments}\n{output}"
        )
    return output


def main():
    if not shutil.which("uv"):
        raise SystemExit("This integration check requires uv; see the U00 lab README.")
    with tempfile.TemporaryDirectory(prefix="js2py-download-") as directory:
        # This archive is built by the repository's explicit allowlist, not user input.
        with zipfile.ZipFile(
            ROOT / "public/learning-assets/js2py/u00-environment.zip"
        ) as archive:
            archive.extractall(directory)
        lab = Path(directory) / "u00-environment"
        run(["uv", "sync", "--locked"], lab)
        output = run(["uv", "run", "--locked", "python", "main.py"], lab)
        assert output.strip() == "Tasks: 3 | Done: 1 | Pending: 2", output
        output = run(["uv", "run", "--locked", "python", "-m", "pytest", "-q"], lab)
        assert "6 passed" in output, output
        print("Downloaded project: application output and six baseline cases PASS")

        output = run(
            [
                "uv",
                "run",
                "--locked",
                "python",
                "-m",
                "pytest",
                "exercises/test_next_task.py",
                "-q",
            ],
            lab,
            expect_failure=True,
        )
        assert "4 failed" in output and "NotImplementedError" in output, output
        print("Exercise starter: four intentional failures verified")
        shutil.copyfile(lab / "solutions/next_task.py", lab / "next_task.py")
        output = run(
            [
                "uv",
                "run",
                "--locked",
                "python",
                "-m",
                "pytest",
                "tests",
                "exercises",
                "-q",
            ],
            lab,
        )
        assert "10 passed" in output, output
        print("Reference answer: all ten baseline/exercise cases PASS")

        manifest = lab / "pyproject.toml"
        manifest.write_text(
            manifest.read_text().replace('version = "0.1.0"', 'version = "0.1.1"')
        )
        output = run(["uv", "sync", "--locked"], lab, expect_failure=True)
        assert "--locked" in output and "lockfile" in output.lower(), output
        print("Stale lockfile: --locked rejects a changed project declaration")

    with tempfile.TemporaryDirectory(prefix="js2py-from-scratch-") as directory:
        run(
            [
                "uv",
                "init",
                "--bare",
                "--vcs",
                "none",
                "--python",
                "3.13",
                "taskboard-lab",
            ],
            directory,
        )
        lab = Path(directory) / "taskboard-lab"
        run(["uv", "python", "pin", "3.13"], lab)
        for name in ["pyproject.toml", "main.py", "tasks.json", "tests/test_main.py"]:
            destination = lab / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / name, destination)
        run(["uv", "sync"], lab)
        output = run(["uv", "run", "--locked", "python", "-m", "pytest", "-q"], lab)
        assert "6 passed" in output, output
        print("From-empty-directory instructions: six baseline cases PASS")


if __name__ == "__main__":
    main()
