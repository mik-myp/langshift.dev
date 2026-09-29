"""Repeat requests against our own standard-library child, then clean up."""
from pathlib import Path
from tools.owned_server import exchange, owned_server


def observe(directory: Path, path: str) -> list[str]:
    lines = []
    with owned_server(directory) as (process, port):
        for target in (path, "/not-here.txt", path):
            status, _, body = exchange(port, target)
            label = body.decode("utf-8").strip() if status == 200 else "missing"
            lines.append(f"{status} {label}")
        lines.append(f"request_done_process_alive={process.poll() is None}")
    lines.append(f"process_stopped={process.poll() is not None}")
    return lines


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    print("\n".join(observe(root / "public", "/hello.txt")))
