"""All DB/API tests own their PostgreSQL cluster. DATABASE_URL is never reused."""
import json
import os
from pathlib import Path
import secrets
import signal
import socket
import subprocess
import sys
import time
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.request import Request, ProxyHandler, build_opener
from client import NoRedirect
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from labdb import OwnedCluster
from models import Base
from security import provision_user

ROOT = Path(__file__).resolve().parents[1]


def migrate(url, revision="head"):
    env = dict(os.environ, DATABASE_URL=url)
    result = subprocess.run([sys.executable, "-m", "alembic", "upgrade", revision],
                            cwd=ROOT, env=env, capture_output=True, text=True, timeout=40)
    assert result.returncode == 0, "Owned database migration failed (inspect sanitized tooling)"


@pytest.fixture(scope="session")
def cluster():
    with OwnedCluster() as owned:
        yield owned


@pytest.fixture(scope="session")
def database(cluster):
    url = cluster.url()
    migrate(url)
    engine = create_engine(url, hide_parameters=True, pool_pre_ping=True)
    with engine.connect() as connection:
        assert connection.scalar(text("SHOW server_version_num")) == "180006"
        assert connection.scalar(text("SHOW listen_addresses")) == ""
        assert connection.scalar(text("SHOW transaction_isolation")) == "read committed"
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def clean(database):
    # Every name comes from our declared metadata, and database is the owned fixture.
    names = ", ".join(Base.metadata.tables)
    with database.begin() as connection:
        connection.execute(text("TRUNCATE " + names + " RESTART IDENTITY CASCADE"))


class API:
    def __init__(self, port, log_path):
        self.port, self.log_path = port, log_path
        self.records, self.secrets = [], []

    def request(self, method, path, body=None, token=None, key=None, raw=None):
        if isinstance(body, dict):
            for name in ("password", "current_password", "new_password"):
                value = body.get(name)
                if isinstance(value, str) and len(value) >= 8:
                    self.secrets.append(value)
        if token and len(token) >= 8:
            self.secrets.append(token)
        headers = {"Content-Type": "application/json"}
        if token is not None:
            headers["Authorization"] = "Bearer " + token
        if key is not None:
            headers["Idempotency-Key"] = key
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        req = Request(f"http://127.0.0.1:{self.port}" + path, data=data, method=method, headers=headers)
        try:
            response = build_opener(ProxyHandler({}), NoRedirect()).open(req, timeout=15)
        except HTTPError as error:
            response = error
        with response:
            raw_body = response.read()
            result = json.loads(raw_body) if raw_body else None
            safe = dict(result) if isinstance(result, dict) else result
            if isinstance(safe, dict) and "access_token" in safe:
                self.secrets.append(safe["access_token"])
                safe["access_token"] = "<redacted>"
            known = {"", "health", "live", "ready", "auth", "token", "logout", "logout-all", "users", "me",
                     "password", "session-count", "projects", "members", "tasks", "summary"}
            visible_path = "/".join(part if part in known or part.isdigit() else "<segment>"
                                    for part in path.split("?", 1)[0].split("/"))
            if "?" in path:
                visible_path += "?<query redacted>"
            self.records.append({"method": method, "path": visible_path, "status": response.status,
                                 "body": safe, "body_bytes": len(raw_body)})
            return SimpleNamespace(status=response.status, body=result, headers=dict(response.headers),
                                   body_bytes=len(raw_body))

    def token(self, login, password):
        self.secrets.append(password)
        result = self.request("POST", "/auth/token", {"login": login, "password": password})
        assert result.status == 200
        return result.body["access_token"]


@pytest.fixture(scope="session")
def api(database, cluster, tmp_path_factory):
    directory = tmp_path_factory.mktemp("owned-api")
    log_path = directory / "server.log"
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = dict(os.environ, DATABASE_URL=cluster.url())
    with log_path.open("w") as stream:
        process = subprocess.Popen([sys.executable, "serve.py", "--port", str(port), "--app", "solutions.project_summary:app"], cwd=ROOT,
            env=env, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        client = API(port, log_path)
        def restart_api():
            nonlocal process
            os.killpg(process.pid, signal.SIGINT)
            process.wait(timeout=15)
            process = subprocess.Popen([sys.executable, "serve.py", "--port", str(port), "--app", "solutions.project_summary:app"],
                cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            for _ in range(150):
                assert process.poll() is None, "Owned API restart failed"
                try:
                    if client.request("GET", "/health/ready").status == 200:
                        return
                except URLError:
                    time.sleep(.05)
            raise AssertionError("Owned API restart timeout")
        client.restart = restart_api
        try:
            for _ in range(150):
                assert process.poll() is None, "Owned API startup failed"
                try:
                    if client.request("GET", "/health/ready").status == 200:
                        break
                except URLError:
                    time.sleep(.05)
            else:
                raise AssertionError("Owned API readiness timeout")
            yield client
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGINT)
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
            output = log_path.read_text()
            assert all(value not in output for value in client.secrets), "Credential appeared in server log"
            assert "Authorization:" not in output
            postgres_output = (cluster.root / "postgres.log").read_text()
            assert all(value not in postgres_output for value in client.secrets), "Credential appeared in PostgreSQL log"
            evidence_dir = Path(os.environ.get("SECURITY_EVIDENCE_DIR", str(directory)))
            evidence_dir.mkdir(parents=True, exist_ok=True)
            evidence = {"lab": ROOT.name, "server_version_num": 180006, "socket_only": True,
                "http_host": "127.0.0.1", "http_port": port, "server_exit": process.returncode,
                "credential_log_scan": "PASS", "postgres_credential_log_scan": "PASS", "http_records": client.records,
                "http_count": len(client.records), "database_root": str(cluster.root)}
            (evidence_dir / (ROOT.name + "-http.json")).write_text(json.dumps(evidence, indent=2))


@pytest.fixture
def accounts(database):
    password = secrets.token_urlsafe(24)
    Session = sessionmaker(database, expire_on_commit=False)
    with Session.begin() as session:
        users = {name: provision_user(session, name, password).id for name in ("Alice", "Bob", "Carol")}
    return SimpleNamespace(password=password, **users)
