"""Same gate locally and in the supplied manual hosted-workflow example."""
import ast
from pathlib import Path
import subprocess
import sys

from ops.cluster import reject_connection_environment

reject_connection_environment()  # Direct ci.py must fail before tests or cluster creation.

if sys.version_info[:3] != (3,13,15):raise SystemExit("Use CPython 3.13.15")
for folder in [Path("ops"),Path("migrations"),Path("tests"),Path("solutions")]:
    if folder.exists():
        for source in folder.rglob("*.py"):ast.parse(source.read_text(),filename=str(source))
subprocess.run([sys.executable,"-m","pytest","-q"],check=True)
subprocess.run([sys.executable,"demo.py"],check=True)
print("LOCAL CI PASS: syntax, PostgreSQL/environment tests, real process drill; not hosted CI or public deployment")
