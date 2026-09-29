#!/usr/bin/env python3
"""Run the actual downloaded local-project chapter integration."""

import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "project_checks", Path(__file__).with_name("js2py-project-checks.py")
)
CHECKS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKS)

if __name__ == "__main__":
    CHECKS.main("local-project")
