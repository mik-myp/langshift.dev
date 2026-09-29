#!/usr/bin/env python3
"""Real PG/API suites, with explicit runtime/env isolation and extracted-lab support."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LABS = ("s01-identity", "s02-authorization", "s03-reliable-operations")
PYTHON_DIR = "/tmp/langshift-js2py-python-20260928"
CACHE_DIR = "/tmp/langshift-js2py-uv-cache-20260928"


def isolated_environment():
    # Keep only the two explicitly controlled uv storage paths; no inherited
    # active interpreter, project environment, index or configuration redirects.
    original = dict(os.environ)
    environment = {name: value for name, value in original.items()
        if not name.upper().startswith(("UV_", "PG")) and name not in
        {"VIRTUAL_ENV", "CONDA_PREFIX", "PYTHONHOME", "PYTHONPATH", "PYTHONUSERBASE", "DATABASE_URL", "PYTEST_ADDOPTS", "PYTEST_PLUGINS"}}
    environment["UV_PYTHON_INSTALL_DIR"] = original.get("UV_PYTHON_INSTALL_DIR", PYTHON_DIR)
    environment["UV_CACHE_DIR"] = original.get("UV_CACHE_DIR", CACHE_DIR)
    environment["UV_NO_CONFIG"] = "true"
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    return environment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lab", choices=LABS)
    parser.add_argument("--lab-root", type=Path, default=os.environ.get("JS2PY_LAB_ROOT"),
        help="One extracted lab root, or a parent containing named lab directories")
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args()
    uv = shutil.which("uv") or str(Path.home() / ".local/bin/uv")
    environment = isolated_environment()
    if args.evidence_dir:
        environment["SECURITY_EVIDENCE_DIR"] = str(args.evidence_dir.resolve())
    base = (args.lab_root or ROOT / "examples/js2py").resolve()
    if (base / "pyproject.toml").is_file():
        declaration = (base / "pyproject.toml").read_text()
        matches = [lab for lab in LABS if f'name = "js2py-{lab}"' in declaration]
        if len(matches) != 1 or (args.lab and args.lab != matches[0]):
            parser.error("Single lab root must identify the selected security lab")
        directories = [(matches[0], base)]
    else:
        directories = [(lab, base / lab) for lab in ((args.lab,) if args.lab else LABS)]
    for lab, directory in directories:
        if not (directory / "uv.lock").is_file() or not (directory / "pyproject.toml").is_file():
            parser.error("Lab root must contain its own declaration and locked environment")
        if (directory / ".venv").is_symlink():
            parser.error("Refusing a lab virtual-environment symlink")
        print(f"RUN {lab}: {directory}", flush=True)
        subprocess.run([uv, "--no-config", "sync", "--locked", "--python", "3.13.15"],
                       cwd=directory, env=environment, check=True)
        subprocess.run([uv, "--no-config", "run", "--locked", "--python", "3.13.15",
                        "python", "-m", "pytest", "-q"],
                       cwd=directory, env=environment, check=True)
    print("PASS: real owned PostgreSQL/API/security suites; inherited uv/libpq redirects excluded")


if __name__ == "__main__":
    main()
