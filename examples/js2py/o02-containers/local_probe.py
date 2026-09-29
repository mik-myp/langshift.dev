"""Host POSIX/HTTP smoke check, explicitly NOT a container test."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
from urllib.error import HTTPError
from urllib.request import ProxyHandler, build_opener

ROOT = Path(__file__).resolve().parent


def observe():
    if os.geteuid() == 0:
        raise RuntimeError("use an ordinary account for the permission failure")
    with TemporaryDirectory(prefix="js2py-o02-host-") as temp:
        data = Path(temp) / "data"
        data.mkdir()
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0)); listener.listen()
        port = listener.getsockname()[1]
        with (Path(temp) / "server.log").open("w") as output:
            process = subprocess.Popen([sys.executable, "-m", "uvicorn", "app:create_app",
                "--factory", "--fd", str(listener.fileno()), "--no-access-log", "--no-proxy-headers"],
                cwd=ROOT, env={"OPS_DATA_DIR": str(data)}, pass_fds=(listener.fileno(),),
                stdout=output, stderr=subprocess.STDOUT)
            listener.close()
            def get(path):
                try:
                    response = build_opener(ProxyHandler({})).open(f"http://127.0.0.1:{port}{path}", timeout=2)
                except HTTPError as exc:
                    response = exc
                with response:
                    return response.status, json.load(response)
            try:
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise RuntimeError("owned local smoke process failed")
                    try:
                        if get("/health/live")[0] == 200:
                            break
                    except OSError:
                        pass
                    time.sleep(.03)
                else:
                    raise TimeoutError("owned local smoke process not ready")
                assert get("/health/ready") == (200, {"status": "ready"})
                data.chmod(0o500)
                try:
                    assert get("/health/live")[0] == 200
                    assert get("/health/ready") == (503, {"status": "not_ready"})
                finally:
                    data.chmod(0o700)
                assert get("/health/ready")[0] == 200
                assert get("/tasks")[0] == 404
            finally:
                if process.poll() is None:
                    process.terminate()
                try:
                    process.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait(timeout=3)
    return ["host_http_live=200", "host_http_ready=200", "unwritable_live=200",
            "unwritable_ready=503", "restored_ready=200", "tasks_not_implemented=404",
            "container_runtime=NOT_VERIFIED"]


if __name__ == "__main__":
    print("\n".join(observe()))
