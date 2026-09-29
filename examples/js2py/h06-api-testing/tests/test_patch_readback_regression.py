"""Prove acceptance rejects the old blind spot, mutating only a disposable copy."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


@pytest.mark.parametrize("target", [
    "tests/test_contract.py::test_patch_note_states",
    "solutions/test_independent.py::test_empty_patch_preserves_non_default_values",
], ids=["base-note-states", "independent-empty-patch"])
def test_readback_acceptance_rejects_stale_response_mutant(tmp_path, target):
    root = Path(__file__).resolve().parents[1]
    copied = tmp_path / "mutant"
    copied.mkdir()
    # Explicit minimal inputs: no .venv, secrets, cache, or recursive test runner.
    for relative in (
        "pyproject.toml", "task_api/__init__.py", "task_api/config.py",
        "task_api/dependencies.py", "task_api/main.py", "task_api/models.py",
        "task_api/routes.py", "task_api/store.py", "tests/conftest.py",
        "tests/test_contract.py", "solutions/test_independent.py",
    ):
        destination = copied / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / relative, destination)
    source = copied / "task_api/store.py"
    before = source.read_text(encoding="utf-8")
    marker = "        candidate = current.model_dump()\n"
    assert before.count(marker) == 1
    defect = (
        "        if not payload.model_fields_set:\n"
        '            self.tasks[current.id] = TaskStored(id=current.id, title="Untitled", '
        'minutes=0, done=False, note=None)\n'
        "            return current\n"
    )
    source.write_text(before.replace(marker, defect + marker), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=short", "-p", "no:cacheprovider", target],
        cwd=copied, env={**os.environ, "PYTHONPATH": str(copied), "PYTEST_ADDOPTS": ""},
        capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    # Failure must be the readback assertion, not import/collection or status noise.
    assert "assert stored.json() == " in result.stdout
    assert "AssertionError" in result.stdout
    assert "1 failed" in result.stdout
    if target.startswith("tests/"):
        assert "2 passed" in result.stdout
    assert (root / "task_api/store.py").read_text(encoding="utf-8") == before
    print(json.dumps({"regression": "stale-response-mutant", "target": target,
                      "child_returncode": result.returncode,
                      "child_stdout": result.stdout, "child_stderr": result.stderr,
                      "canonical_store_unchanged": True}))
