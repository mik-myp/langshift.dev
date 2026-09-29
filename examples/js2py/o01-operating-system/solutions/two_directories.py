"""Independent requirement: two explicit data roots must not share state."""
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


def observe() -> list[int]:
    with TemporaryDirectory(prefix="js2py-independent-") as temp:
        first, second = Path(temp) / "first", Path(temp) / "second"
        first.mkdir(); second.mkdir()
        for directory in (first, first, second):
            subprocess.run([sys.executable, str(ROOT / "worker.py"), "--once"],
                cwd=second, env={"OPS_DATA_DIR": str(directory)},
                check=True, capture_output=True, timeout=3)
        return [json.loads((directory / "state.json").read_text())["starts"] for directory in (first, second)]


if __name__ == "__main__":
    print(observe())
