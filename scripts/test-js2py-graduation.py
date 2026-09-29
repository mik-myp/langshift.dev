"""Check the G01 material package, never a student's backend or graduation."""

import hashlib
import json
import os
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    lab = "g01-graduation"
    source = ROOT / "examples/js2py" / lab
    names = json.loads((source.parent / (lab + "-files.json")).read_text())
    archive_path = ROOT / "public/learning-assets/js2py" / (lab + ".zip")
    output = Path(tempfile.mkdtemp(prefix="js2py-graduation-materials-"))
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.namelist() == [f"{lab}/{name}" for name in names]
        for name in names:
            assert not Path(name).is_absolute() and ".." not in Path(name).parts
            assert archive.read(f"{lab}/{name}") == (source / name).read_bytes()
        archive.extractall(output)
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("PYTHON")
    }
    for key in ("VIRTUAL_ENV", "UV_ACTIVE", "UV_PYTHON", "UV_PROJECT_ENVIRONMENT"):
        env.pop(key, None)
    env.update(PYTHONNOUSERSITE="1", PYTHONIOENCODING="utf-8", UV_NO_CONFIG="1")
    records = []
    for iteration in range(2):
        for args in (
            ["--version"],
            ["check_evidence.py", "templates/evidence.json"],
            ["-m", "unittest", "discover", "-s", "tests", "-v"],
        ):
            command = [
                "uv",
                "run",
                "--no-project",
                "--python",
                "3.13.15",
                "python",
                *args,
            ]
            result = subprocess.run(
                command,
                cwd=output / lab,
                env=env,
                capture_output=True,
                text=True,
                timeout=90,
            )
            records.append(
                {
                    "iteration": iteration + 1,
                    "command": command,
                    "exit": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            )
            (output / "commands.json").write_text(json.dumps(records, indent=2) + "\n")
            assert result.returncode == 0, records[-1]
            if args == ["--version"]:
                assert result.stdout.strip() == "Python 3.13.15"
            elif args[0] == "check_evidence.py":
                report = json.loads(result.stdout)
                assert report["format_valid"]
                assert report["scenario_status_counts"] == {
                    "blocked": 0,
                    "fail": 0,
                    "not_run": 24,
                    "pass": 0,
                }
                for flag in (
                    "artifact_files_verified",
                    "backend_verified",
                    "graduation_awarded",
                    "public_operation_verified",
                ):
                    assert report[flag] is False
            else:
                assert re.search(r"Ran 15 tests\b", result.stderr)
                assert result.stderr.rstrip().endswith("OK")
    for name in names:
        assert (source / name).read_bytes() == (output / lab / name).read_bytes()
    print(
        "PASS G01: 15 material tests repeated twice; templates unchanged; "
        "24 student scenarios not_run; NO backend/graduation/public-operation approval"
    )
    print(
        f"ZIP sha256={hashlib.sha256(archive_path.read_bytes()).hexdigest()}; evidence={output}"
    )


if __name__ == "__main__":
    main()
