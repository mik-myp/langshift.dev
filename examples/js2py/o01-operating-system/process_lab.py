"""Bounded experiments; signals are sent ONLY to this function's own child."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory
import time

ROOT = Path(__file__).resolve().parent


@contextmanager
def owned_worker(directory: Path):
    log_path = directory / "worker.log"
    with log_path.open("w") as output:
        process = subprocess.Popen(
            [sys.executable, "-u", str(ROOT / "worker.py")],
            cwd=directory, env={"OPS_DATA_DIR": str(directory)},
            stdout=output, stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("owned worker failed before ready")
                if "ready pid=" in log_path.read_text():
                    yield process
                    break
                time.sleep(0.02)
            else:
                raise TimeoutError("owned worker did not become ready")
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)


def signal_case(name: str) -> tuple[int, bool]:
    chosen = {"SIGTERM": signal.SIGTERM, "SIGINT": signal.SIGINT, "SIGKILL": signal.SIGKILL}[name]
    with TemporaryDirectory(prefix="js2py-signal-") as temp:
        directory = Path(temp)
        with owned_worker(directory) as process:
            process.send_signal(chosen)
            code = process.wait(timeout=3)
        return code, (directory / "stopped.txt").exists()


def observe() -> list[str]:
    missing = subprocess.run([sys.executable, str(ROOT / "worker.py"), "--once"],
                             env={}, capture_output=True, text=True, timeout=3)
    lines = [f"missing_config_exit={missing.returncode}"]
    for name in ("SIGTERM", "SIGINT", "SIGKILL"):
        code, cleaned = signal_case(name)
        lines.append(f"{name}: subprocess_returncode={code} cleanup={cleaned}")
    with TemporaryDirectory(prefix="js2py-restart-") as temp:
        for _ in range(2):
            subprocess.run([sys.executable, str(ROOT / "worker.py"), "--once"],
                           cwd=temp, env={"OPS_DATA_DIR": temp}, check=True,
                           capture_output=True, timeout=3)
        count = json.loads((Path(temp) / "state.json").read_text())["starts"]
        lines.append(f"same_directory_across_processes={count}")
    return lines


if __name__ == "__main__":
    print("\n".join(observe()))
