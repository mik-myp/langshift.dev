from contextlib import contextmanager
import os
import re
import socket
import subprocess
import sys
import tempfile
import time

import httpx

from ops.cluster import checked_root, reject_connection_environment


@contextmanager
def running(root, release="v1", database="source", factory="ops.app:create_app"):
    reject_connection_environment()
    checked_root(str(root))
    env = {
        key: value for key, value in os.environ.items()
        if key not in {"DATABASE_URL", "OPS_LOG_FILE", "WEB_CONCURRENCY"}
        and not key.startswith("UVICORN_")
    }
    env.update(OPS_LAB_ROOT=str(root), OPS_DATABASE=database, OPS_RELEASE=release)
    # Each child owns a distinct private log, even for concurrent identical releases.
    with tempfile.NamedTemporaryFile(
        mode="w", prefix=f"service-{release}-{database}-", suffix=".log",
        dir=root, delete=False,
    ) as output:
        logpath = root / os.path.basename(output.name)
        logpath.chmod(0o600)
        child = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", factory, "--factory",
             "--host", "127.0.0.1", "--port", "0", "--workers", "1",
             "--no-access-log", "--no-use-colors", "--log-level", "info",
             "--no-proxy-headers"],
            env=env, stdout=output, stderr=output,
        )
        port = None
        try:
            deadline = time.monotonic() + 10
            # Uvicorn binds port0 itself. There is no probe-close-rebind window.
            # This parser is checked against the pinned Uvicorn startup banner;
            # a future format change must fail closed, not guess another port.
            while port is None:
                if child.poll() is not None:
                    raise RuntimeError("Owned application failed to start; inspect private service diagnostics")
                banner = re.search(
                    r"^INFO:\s+Uvicorn running on http://127\.0\.0\.1:([0-9]+) ",
                    logpath.read_text(), re.MULTILINE,
                )
                if banner:
                    port = int(banner.group(1))
                    if not 1 <= port <= 65535:
                        raise RuntimeError("Unexpected owned Uvicorn port")
                    break
                if time.monotonic() > deadline:
                    raise RuntimeError("Owned Uvicorn startup banner deadline exceeded")
                time.sleep(.05)
            with httpx.Client(
                base_url=f"http://127.0.0.1:{port}", timeout=5, trust_env=False,
            ) as client:
                while True:
                    if child.poll() is not None:
                        raise RuntimeError("Owned application exited before readiness")
                    try:
                        if client.get("/health/ready").status_code == 200:
                            break
                    except httpx.TransportError:
                        pass
                    if time.monotonic() > deadline:
                        raise RuntimeError("Readiness deadline exceeded")
                    time.sleep(.05)
                yield client
        finally:
            if child.poll() is None:
                child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
        if port is not None:
            with socket.socket() as probe:
                assert probe.connect_ex(("127.0.0.1", port)) != 0, "Former owned API port still open"
