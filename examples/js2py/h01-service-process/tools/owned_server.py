"""Start ONLY our child, on IPv4 loopback, and stop ONLY that child.

Maintenance/test infrastructure: students need not recreate subprocess control.
Port 0 lets the OS allocate a free port without a find-then-bind race.
The CPython 3.13.15 CLI banner supplies that port. No custom HTTP handler.
"""
from contextlib import contextmanager
from http.client import HTTPConnection
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
import time


def stop_owned(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)


@contextmanager
def owned_server(directory: Path):
    directory = directory.absolute()
    if not directory.is_dir():
        raise ValueError("serving directory must exist")
    if directory.is_symlink() or any(p.is_symlink() for p in directory.rglob("*")):
        raise ValueError("do not serve symbolic links")
    with TemporaryDirectory(prefix="js2py-owned-http-") as temporary:
        log_path = Path(temporary) / "server.log"
        with log_path.open("w", encoding="utf-8") as output:
            process = subprocess.Popen(
                [sys.executable, "-u", "-m", "http.server", "0",
                 "--bind", "127.0.0.1", "--directory", str(directory)],
                cwd=temporary, stdout=output, stderr=subprocess.STDOUT,
            )
            try:
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline:
                    log = log_path.read_text(encoding="utf-8")
                    if process.poll() is not None:
                        raise RuntimeError(f"owned server exited during startup:\n{log}")
                    match = re.search(r"Serving HTTP on 127\.0\.0\.1 port (\d+)", log)
                    if match:
                        yield process, int(match.group(1))
                        break
                    time.sleep(0.02)
                else:
                    raise TimeoutError("owned server did not announce its port")
            finally:
                stop_owned(process)


def exchange(port: int, path: str, method="GET", body=None, headers=None):
    """Bounded client request. No redirects, proxies, or external destinations."""
    connection = HTTPConnection("127.0.0.1", port, timeout=3)
    try:
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        data = response.read()
        return response.status, dict(response.getheaders()), data
    finally:
        connection.close()
