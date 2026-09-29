"""Reconstruct H01/H02 from public ZIPs and verify only owned local services.

This is maintainer infrastructure, not an H01 prerequisite. No system services,
user databases, external hosts, or source files are changed.
"""

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
    output = Path(tempfile.mkdtemp(prefix="js2py-service-contracts-"))
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    for key in ("VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT", "UV_ACTIVE", "UV_PYTHON"):
        env.pop(key, None)
    env.update(PYTHONIOENCODING="utf-8", PYTHONNOUSERSITE="1", UV_NO_CONFIG="1")
    records = []
    labs = [
        (
            "h01-service-process",
            "solutions/test_health.py",
            13,
            2,
            ["one_shot.py", "observe.py"],
        ),
        (
            "h02-http-contract",
            "solutions/test_review_cases.py",
            47,
            5,
            ["contract_examples.py", "inspect_transport.py"],
        ),
    ]
    for lab, solution, main_count, answer_count, scripts in labs:
        names = json.loads((ROOT / f"examples/js2py/{lab}-files.json").read_text())
        archive_path = ROOT / f"public/learning-assets/js2py/{lab}.zip"
        with zipfile.ZipFile(archive_path) as archive:
            assert archive.namelist() == [f"{lab}/{name}" for name in names]
            for name in names:
                assert not Path(name).is_absolute() and ".." not in Path(name).parts
                assert (
                    archive.read(f"{lab}/{name}")
                    == (ROOT / "examples/js2py" / lab / name).read_bytes()
                )
            archive.extractall(output)
        directory = output / lab
        before = (directory / "uv.lock").read_bytes()
        commands = [
            (
                [
                    "uv",
                    "sync",
                    "--locked",
                    "--default-index",
                    "https://pypi.org/simple",
                ],
                0,
            ),
            (["uv", "run", "--locked", "python", "--version"], 0),
        ]
        commands.extend((["uv", "run", "--locked", "python", s], 0) for s in scripts)
        commands.extend(
            [
                (["uv", "run", "--locked", "python", "-m", "pytest", "-q"], 0),
                (
                    ["uv", "run", "--locked", "python", "-m", "pytest", "-q", solution],
                    0,
                ),
            ]
        )
        if lab.startswith("h01"):
            commands.append(
                (
                    [
                        "uv",
                        "run",
                        "--locked",
                        "python",
                        "-m",
                        "solutions.observe_health",
                    ],
                    0,
                )
            )
        else:
            commands.append(
                (
                    [
                        "uv",
                        "run",
                        "--locked",
                        "python",
                        "-m",
                        "pytest",
                        "-q",
                        "errors/test_wrong_contract.py",
                    ],
                    1,
                )
            )
        for command, expected in commands:
            result = subprocess.run(
                command,
                cwd=directory,
                env=env,
                text=True,
                capture_output=True,
                timeout=120,
            )
            records.append(
                {
                    "lab": lab,
                    "command": command,
                    "expected": expected,
                    "exit": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            )
            (output / "commands.json").write_text(json.dumps(records, indent=2) + "\n")
            assert result.returncode == expected, records[-1]
            if command[-1] == "--version":
                assert result.stdout.strip() == "Python 3.13.15"
            if "pytest" in command and expected == 0:
                count = answer_count if command[-1] == solution else main_count
                assert re.search(rf"\b{count} passed\b", result.stdout), result.stdout
            if command[-1] in ("observe.py", "solutions.observe_health"):
                assert "request_done_process_alive=True" in result.stdout
                assert "process_stopped=True" in result.stdout
            if command[-1] == "inspect_transport.py":
                assert "real POST tasks: HTTP 501; no CRUD implemented" in result.stdout
                assert "owned_service_stopped=True" in result.stdout
            if expected == 1:
                assert "1 failed" in result.stdout and "AssertionError" in result.stdout
        assert before == (directory / "uv.lock").read_bytes()
        print(
            f"PASS {lab}: {main_count}+{answer_count} tests, unchanged lock; "
            f"ZIP sha256={hashlib.sha256(archive_path.read_bytes()).hexdigest()}"
        )
    print(
        f"PASS 67 learner tests; H02 intentional mismatch detected; evidence: {output}"
    )


if __name__ == "__main__":
    main()
