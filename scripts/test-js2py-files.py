#!/usr/bin/env python3
"""Verify L07's downloaded bytes, real uv commands and independent reconstruction."""

import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UV = ["uv", "run", "--no-project", "--python", "3.13", "python"]
SPEC = importlib.util.spec_from_file_location(
    "l07_checks", ROOT / "scripts/tests/test_js2py_files.py"
)
CHECKS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKS)


def successful(lab, args, cwd="."):
    result = CHECKS.execute(lab, args, cwd=cwd, prefix=UV)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout


def main():
    if not shutil.which("uv"):
        raise SystemExit("This maintainer integration check needs uv and Python 3.13.")
    check = unittest.TestCase()
    with tempfile.TemporaryDirectory(prefix="js2py-files-integration-") as directory:
        parent = Path(directory).resolve()
        (parent / "pyproject.toml").write_text(
            '[project]\nname = "must-not-be-used"\nversion = "0.0.0"\nrequires-python = ">=99"\n'
        )
        (parent / "uv.lock").write_text("deliberately incompatible parent lock\n")
        parents = {
            name: (parent / name).read_bytes() for name in ["pyproject.toml", "uv.lock"]
        }
        # Only this trusted, allowlisted artifact; not an arbitrary uploaded ZIP.
        with zipfile.ZipFile(
            ROOT / "public/learning-assets/js2py/u07-files.zip"
        ) as archive:
            archive.extractall(parent)
        lab = parent / "u07-files"
        version = successful(lab, ["--version"]).strip()
        assert version.startswith("Python 3.13."), version
        for case in CHECKS.CASES:
            CHECKS.assert_case(check, lab, case, prefix=UV)
        CHECKS.verify_tree(check, lab)
        assert all(
            (parent / name).read_bytes() == data for name, data in parents.items()
        )
        assert {p.name for p in parent.iterdir()} == {"u07-files", *parents}
        assert not any(p.name == ".venv" for p in parent.rglob("*"))
        print(
            f"Downloaded L07: {version}; 33 ordered scenarios, 8 expected failures PASS",
            flush=True,
        )
        print(
            "38 source/fixture entries unchanged; 10 exact outputs; incompatible parent ignored; bounded caches only",
            flush=True,
        )

        scratch = parent / "my_tasks"
        scratch.mkdir()
        assert not list(scratch.iterdir())
        reconstructed = []
        for name in CHECKS.NAMES:
            prefix = "solutions/independent/"
            if name.startswith(prefix):
                target = scratch / name.removeprefix(prefix)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((lab / name).read_bytes())
                reconstructed.append(target)
        assert len(reconstructed) == 6
        sources = {p: p.read_bytes() for p in reconstructed}
        output = scratch / "_output/tasks.json"
        probe = next(c for c in CHECKS.CASES if c["id"] == "independent-import")
        CHECKS.assert_case(check, scratch, dict(probe, cwd="."), prefix=UV)
        assert not output.parent.exists()
        for identifier in ["independent-first", "independent-again"]:
            case = next(c for c in CHECKS.CASES if c["id"] == identifier)
            CHECKS.assert_case(check, scratch, dict(case, cwd="."), prefix=UV)
        expected = CHECKS.FIXTURES["outputs"][
            "solutions/independent/_output/tasks.json"
        ]
        assert output.read_bytes() == expected.encode("utf-8")
        repeated = successful(parent, [str(scratch / "run_store.py")])
        assert repeated.startswith(
            "Source: existing file\nSaved: 2\nPending minutes: 35\n"
        )
        assert not (parent / "_output").exists()
        output.write_text(
            expected.replace('"minutes": 35', '"minutes": 36'), encoding="utf-8"
        )
        changed = successful(scratch, ["-m", "task_store.app"])
        assert "Pending minutes: 36\n" in changed
        assert json.loads(output.read_text())[1]["minutes"] == 36
        output.write_text("[]\n", encoding="utf-8")
        empty = successful(scratch, ["-m", "task_store.app"])
        assert (
            empty == "Source: existing file\nSaved: 0\nPending minutes: 0\nTasks: []\n"
        )
        assert output.read_bytes() == b"[]\n"
        output.write_bytes(b"{broken\n")
        failure = CHECKS.execute(scratch, ["-m", "task_store.app"], prefix=UV)
        assert failure.returncode != 0 and "JSONDecodeError" in failure.stderr
        assert failure.stdout == "Invalid JSON; file unchanged\n"
        assert output.read_bytes() == b"{broken\n"
        assert all(p.read_bytes() == data for p, data in sources.items())
        assert all(
            (parent / name).read_bytes() == data for name, data in parents.items()
        )
        print(
            "Empty-directory reconstruction: import, first/repeated process, different cwd, changed/empty/corrupt data PASS",
            flush=True,
        )

        interpreter = successful(
            lab, ["-c", "import sys; print(sys.executable)"]
        ).strip()
        subprocess.run(
            [
                interpreter,
                "-m",
                "unittest",
                "discover",
                "-s",
                "scripts/tests",
                "-p",
                "test_js2py_files.py",
                "-v",
            ],
            cwd=ROOT,
            env=dict(CHECKS.environment(), JS2PY_PYTHON=interpreter),
            check=True,
            timeout=180,
        )
        print(
            "20 L07 tests under the actual interpreter: validation matrix, resource closure, fault propagation and non-atomic-write boundary PASS",
            flush=True,
        )


if __name__ == "__main__":
    main()
