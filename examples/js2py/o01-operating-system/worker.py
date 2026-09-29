"""Single-process disposable-data worker. Not a durable queue or database."""
import argparse
import json
import os
from pathlib import Path
import signal
import sys
import time


def data_directory(environ) -> Path:
    raw = environ.get("OPS_DATA_DIR", "")
    directory = Path(raw)
    if not raw or not directory.is_absolute() or not directory.is_dir():
        raise ValueError("OPS_DATA_DIR must name an existing absolute directory")
    return directory


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    try:
        directory = data_directory(os.environ)
    except ValueError:
        print("configuration error: OPS_DATA_DIR must name an existing absolute directory", file=sys.stderr)
        return 78
    stop_requested = False

    def request_stop(signum, frame):
        nonlocal stop_requested
        stop_requested = True  # Keep handlers small: normal control flow does cleanup.

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    state = directory / "state.json"
    try:
        old = json.loads(state.read_text()) if state.exists() else {"starts": 0}
        if not isinstance(old, dict) or type(old.get("starts")) is not int or old["starts"] < 0:
            raise ValueError("invalid state")
        pending = directory / "state.pending"
        pending.write_text(json.dumps({"starts": old["starts"] + 1}) + "\n")
        pending.replace(state)  # Single writer only; not a power-loss durability proof.
        print(f"ready pid={os.getpid()} starts={old['starts'] + 1}", flush=True)
        try:
            if not args.once:
                while not stop_requested:
                    time.sleep(0.05)
        finally:
            (directory / "stopped.txt").write_text("normal cleanup\n")
            print("cleanup complete", flush=True)
    except (ValueError, json.JSONDecodeError):
        print("data error: invalid teaching state", file=sys.stderr)
        return 65
    except OSError:
        print("I/O error: teaching state is not writable", file=sys.stderr)
        return 74
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
