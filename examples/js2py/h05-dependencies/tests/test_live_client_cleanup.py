"""Maintainer regression: real sockets, temporary fault app, never a user server."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.request import ProxyHandler, build_opener

import pytest


FAULT_APP = """
import sys
import uvicorn
from fastapi import HTTPException, Request
from task_api.config import Settings
from task_api.dependencies import get_store
from task_api.main import create_app

app = create_app(Settings("Owned cleanup regression"))
body_failure = sys.argv[1] == "1"

def controlled_store(request: Request):
    if request.method == "DELETE":
        print(f"DELETE ATTEMPT {request.url.path}", flush=True)
        if request.url.path == "/tasks/1":
            raise HTTPException(status_code=503, detail="Deliberate first-delete failure")
    if body_failure and request.url.path == "/tasks/99999":
        raise HTTPException(status_code=503, detail="Deliberate body failure")
    return app.state.store

app.dependency_overrides[get_store] = controlled_store
# Port 0 lets the OS choose an unused port; no bind-close-rebind race.
uvicorn.run(app, host="127.0.0.1", port=0, log_level="info")
"""


@pytest.mark.parametrize("body_failure", [False, True], ids=["cleanup-only", "body-and-cleanup"])
def test_cleanup_continues_and_preserves_primary_failure(tmp_path, body_failure):
    root = Path(__file__).resolve().parents[1]
    log_path = tmp_path / "owned-server.log"
    environment = {**os.environ, "PYTHONPATH": str(root),
                   "NO_PROXY": "127.0.0.1,localhost", "no_proxy": "127.0.0.1,localhost"}
    opener = build_opener(ProxyHandler({}))
    with log_path.open("w", encoding="utf-8") as log:
        server = subprocess.Popen(
            [sys.executable, "-u", "-c", FAULT_APP, str(int(body_failure))],
            cwd=root, env=environment, stdout=log, stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 15
            while True:
                output = log_path.read_text(encoding="utf-8")
                assert server.poll() is None, output
                address = re.search(r"Uvicorn running on http://127[.]0[.]0[.]1:(\d+)", output)
                if address:
                    port = int(address.group(1))
                    break
                assert time.monotonic() < deadline, output
                time.sleep(0.03)
            base = f"http://127.0.0.1:{port}"
            # The startup log precedes serving very slightly; bound readiness too.
            while True:
                try:
                    with opener.open(base + "/health", timeout=1) as response:
                        assert response.status == 200
                    break
                except OSError:
                    assert time.monotonic() < deadline, log_path.read_text(encoding="utf-8")
                    time.sleep(0.03)
            result = subprocess.run(
                [sys.executable, "live_client.py", "--port", str(port)],
                cwd=root, env=environment, capture_output=True, text=True, timeout=20,
            )
            assert result.returncode != 0, result.stdout + result.stderr
            assert "CLEANUP FAILED (unconfirmed owned IDs): id=1:" in result.stderr
            assert "503" in result.stderr
            assert "id=2:" not in result.stderr
            assert "LIVE PASS: cleanup and subsequent 404" not in result.stdout
            with opener.open(base + "/tasks", timeout=2) as response:
                remaining = json.load(response)
            assert remaining["total"] == 1
            assert [task["id"] for task in remaining["items"]] == [1]
            attempts = [line for line in log_path.read_text(encoding="utf-8").splitlines()
                        if line.startswith("DELETE ATTEMPT ")]
            assert attempts == ["DELETE ATTEMPT /tasks/1", "DELETE ATTEMPT /tasks/2"]
            if body_failure:
                # Cleanup is printed, but must not replace the original traceback.
                assert 'assert send("GET", "/tasks/99999")' in result.stderr
                assert result.stderr.rstrip().endswith("AssertionError")
                assert "RuntimeError: CLEANUP FAILED" not in result.stderr
            else:
                assert "LIVE PASS: CRUD" in result.stdout
                assert "RuntimeError: CLEANUP FAILED" in result.stderr
        finally:
            if server.poll() is None:
                server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
        assert server.poll() is not None
    print(json.dumps({
        "regression": "owned-client-cleanup", "body_failure": body_failure,
        "port": port, "server_pid": server.pid, "server_stopped": True,
        "server_returncode": server.returncode, "client_returncode": result.returncode,
        "client_stdout": result.stdout, "client_stderr": result.stderr,
        "delete_attempts": attempts, "remaining_ids_before_server_stop": [1],
        "note": "Remaining task belongs only to this stopped in-memory fault app.",
    }))
