"""Real loopback HTTP, reserved ephemeral socket, owned Uvicorn process cleanup."""
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--serve-fd":
        import uvicorn
        with socket.socket(fileno=int(sys.argv[2])) as listener:
            server = uvicorn.Server(uvicorn.Config("api:application", factory=True,
                                                  log_level="warning"))
            server.run(sockets=[listener])
        return
    from bootstrap import main as bootstrap
    bootstrap()
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(16)
        port = listener.getsockname()[1]
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                                    "--serve-fd", str(listener.fileno())],
                                   pass_fds=(listener.fileno(),))
        def request(path, body=None):
            data = None if body is None else json.dumps(body).encode()
            req = Request(f"http://127.0.0.1:{port}{path}", data=data,
                          headers={"Content-Type": "application/json"})
            try:
                response = urlopen(req, timeout=2)
            except HTTPError as error:
                response = error
            with response:
                return response.status, json.load(response)
        try:
            deadline = time.monotonic() + 15
            while True:
                if process.poll() is not None:
                    raise RuntimeError("Uvicorn exited before becoming ready")
                try:
                    if request("/projects")[0] == 200:
                        break
                except (URLError, TimeoutError):
                    pass
                if time.monotonic() >= deadline:
                    raise TimeoutError("Uvicorn readiness timed out")
                time.sleep(0.05)
            status, project = request("/projects", {"name": "Loopback", "owner_id": 1})
            assert status == 201
            status, error = request("/projects", {"name": "Rejected", "owner_id": 999999999})
            assert status == 409 and error == {"detail": "Database rule rejected this write"}
            status, rows = request("/projects")
            assert status == 200 and rows == [project]
            print("loopback HTTP: 201 then 409 then 200; committed project preserved")
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            print("uvicorn stopped:", process.poll() is not None)


if __name__ == "__main__":
    main()
