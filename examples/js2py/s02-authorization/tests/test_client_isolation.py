"""Only owned loopback listeners and synthetic credentials; no real proxy/secret."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import threading
from urllib.request import getproxies_environment
from client import request
from labdb import OwnedCluster


@contextmanager
def listener(records, redirect=None):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            return  # Never write synthetic credential bodies/headers to logs.

        def do_GET(self):
            data = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            records.append((self.path, data, self.headers.get("Authorization")))
            payload = b'{"ok":true}'
            self.send_response(307 if self.path == "/redirect" else 200)
            if self.path == "/redirect":
                self.send_header("Location", redirect)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        do_POST = do_GET

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_port
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


def test_client_ignores_proxy_environment_and_never_follows_redirect(monkeypatch, tmp_path):
    proxy_records, target_records, redirect_records = [], [], []
    password, bearer = secrets.token_urlsafe(24), secrets.token_urlsafe(32)
    with listener(proxy_records) as proxy, listener(redirect_records) as redirected:
        with listener(target_records, f"http://127.0.0.1:{redirected}/capture") as target:
            for key in ("http_proxy", "https_proxy", "all_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
                monkeypatch.setenv(key, f"http://127.0.0.1:{proxy}")
            for key in ("no_proxy", "NO_PROXY"):
                monkeypatch.delenv(key, raising=False)
            assert getproxies_environment()["http"] == f"http://127.0.0.1:{proxy}"
            assert "no_proxy" not in os.environ and "NO_PROXY" not in os.environ
            assert request(target, "POST", "/auth/token", {"password": password})[0] == 200
            assert request(target, "GET", "/users/me", token=bearer)[0] == 200
            assert request(target, "POST", "/redirect", {"password": password}, bearer)[0] == 307
    assert len(target_records) == 3
    assert json.loads(target_records[0][1]) == {"password": password}
    assert target_records[1][2] == "Bearer " + bearer
    assert len(proxy_records) == 0, "A credential-bearing request reached the fake proxy"
    assert len(redirect_records) == 0, "A credential-bearing request followed a redirect"
    directory = Path(os.environ.get("SECURITY_EVIDENCE_DIR", str(tmp_path)))
    directory.mkdir(parents=True, exist_ok=True)
    lab = Path(__file__).resolve().parents[1].name
    (directory / (lab + "-client-isolation.json")).write_text(json.dumps({
        "target_requests": 3, "proxy_requests": 0, "redirect_target_requests": 0,
        "proxy_environment_present": True, "no_proxy_absent": True,
        "credentials": "synthetic; values not recorded", "listeners": "owned 127.0.0.1 only"}, indent=2))


def test_owned_postgres_ignores_implicit_libpq_environment(monkeypatch, tmp_path):
    # A nonexistent service and loopback hostaddr cannot redirect the explicit socket.
    injected = {"PGHOSTADDR": "127.0.0.1", "PGHOST": "127.0.0.1", "PGPORT": "1",
                "PGSERVICE": "nonexistent-lab-service", "PGSERVICEFILE": str(tmp_path / "absent.conf"),
                "PGUSER": "not-the-lab-owner", "PGDATABASE": "not-the-lab-db",
                "PGPASSWORD": secrets.token_urlsafe(24), "PGOPTIONS": "-c statement_timeout=1"}
    for key, value in injected.items():
        monkeypatch.setenv(key, value)
    with OwnedCluster() as cluster:
        assert not any(name.upper().startswith("PG") for name in os.environ)
        owned_root = cluster.root
        cluster.restart()
    assert not owned_root.exists()
