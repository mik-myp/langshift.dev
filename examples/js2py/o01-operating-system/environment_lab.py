"""Inspect only a fictional OPS_LABEL; never dump the real environment."""
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


def observe() -> list[str]:
    with TemporaryDirectory(prefix="js2py-cwd-") as temp:
        directory = Path(temp) / "with-message"
        empty = Path(temp) / "empty"
        directory.mkdir()
        empty.mkdir()
        (directory / "message.txt").write_text("from the working directory\n")
        code = (
            "import os; from pathlib import Path; "
            "print(os.environ.get('OPS_LABEL', 'missing')); "
            "print(Path('message.txt').read_text().strip()); "
            "os.environ['OPS_LABEL']='child-only'"
        )
        configured = {"OPS_LABEL": "parent-choice"}
        result = subprocess.run([sys.executable, "-c", code], cwd=directory,
                                env=configured, text=True, capture_output=True, timeout=3, check=True)
        missing = subprocess.run([sys.executable, "-c", "from pathlib import Path; Path('message.txt').read_text()"],
                                 cwd=empty, env={}, text=True, capture_output=True, timeout=3)
        return result.stdout.splitlines() + [
            f"parent_mapping_unchanged={configured['OPS_LABEL'] == 'parent-choice'}",
            f"wrong_cwd_exit={missing.returncode}",
            f"wrong_cwd_is_FileNotFoundError={'FileNotFoundError' in missing.stderr}",
        ]


if __name__ == "__main__":
    print("\n".join(observe()))
