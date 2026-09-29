#!/usr/bin/env python3
"""Verify L06's actual uv commands, ZIP, import safety and empty reconstruction."""

import importlib.util
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UV = ["uv", "run", "--no-project", "--python", "3.13", "python"]
SPEC = importlib.util.spec_from_file_location(
    "l06_checks", ROOT / "scripts/tests/test_js2py_modules.py"
)
CHECKS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKS)


def successful(lab, args):
    result = CHECKS.execute(lab, args, prefix=UV)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout


def main():
    if not shutil.which("uv"):
        raise SystemExit("This maintainer integration check needs uv and Python 3.13.")
    check = unittest.TestCase()
    with tempfile.TemporaryDirectory(prefix="js2py-modules-integration-") as directory:
        parent = Path(directory)
        (parent / "pyproject.toml").write_text(
            '[project]\nname = "must-not-be-used"\nversion = "0.0.0"\nrequires-python = ">=99"\n'
        )
        (parent / "uv.lock").write_text("deliberately incompatible parent lock\n")
        parents = {
            name: (parent / name).read_bytes() for name in ["pyproject.toml", "uv.lock"]
        }
        # Trusted checked-in allowlisted artifact, not arbitrary uploaded archives.
        with zipfile.ZipFile(
            ROOT / "public/learning-assets/js2py/u06-modules.zip"
        ) as archive:
            archive.extractall(parent)
        lab = parent / "u06-modules"
        sources = {name: (lab / name).read_bytes() for name in CHECKS.NAMES}
        version = successful(lab, ["--version"]).strip()
        assert version.startswith("Python 3.13."), version
        for case in CHECKS.CASES:
            CHECKS.assert_case(check, lab, case, prefix=UV)
        assert all((lab / name).read_bytes() == data for name, data in sources.items())
        assert all(
            (parent / name).read_bytes() == data for name, data in parents.items()
        )
        allowed = {"u06-modules/" + name for name in sources} | set(parents)
        extras = {
            str(p.relative_to(parent)) for p in parent.rglob("*") if p.is_file()
        } - allowed
        for name in extras:
            path = Path(name)
            assert path.parts[0] == "u06-modules" and path.parent.name == "__pycache__"
            assert path.suffix == ".pyc"
            original = path.parent.parent / (path.name.split(".", 1)[0] + ".py")
            assert str(original) in allowed, name
        assert not any(p.name == ".venv" for p in parent.rglob("*"))
        print(
            f"Downloaded L06: {version}; 28 entry scenarios, 8 expected failures PASS"
        )
        print(
            "Incompatible parent project ignored; source unchanged; only bounded bytecode caches created"
        )

        scratch = parent / "my_plan"
        scratch.mkdir()
        assert not list(scratch.iterdir())
        for name, data in sources.items():
            prefix = "solutions/independent/"
            if name.startswith(prefix):
                target = scratch / name.removeprefix(prefix)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
        for case in CHECKS.CASES:
            if case["id"] in {
                "independent-import",
                "independent-entry",
                "independent-direct-fails",
            }:
                CHECKS.assert_case(check, scratch, dict(case, cwd="."), prefix=UV)
        app = scratch / "study_plan/app.py"
        app.write_text(
            app.read_text().replace(
                "plan = build_plan(rows)", "plan = build_plan(rows, budget=40)"
            )
        )
        output = successful(scratch, ["-m", "study_plan.app"])
        assert (
            "'title': 'Practice', 'minutes': 35" in output and "Total: 55\n" in output
        )
        print(
            "Empty-directory reconstruction, import probe, package context and budget variation PASS"
        )

        interpreter = successful(
            lab, ["-c", "import sys; print(sys.executable)"]
        ).strip()
        env = dict(CHECKS.controlled_environment(), JS2PY_PYTHON=interpreter)
        subprocess.run(
            [
                interpreter,
                "-m",
                "unittest",
                "discover",
                "-s",
                "scripts/tests",
                "-p",
                "test_js2py_modules.py",
                "-v",
            ],
            cwd=ROOT,
            env=env,
            check=True,
            timeout=180,
        )
        print(
            "Planner matrix: 340 combinations + 24 order permutations; import sentinel and failure boundaries PASS"
        )


if __name__ == "__main__":
    main()
