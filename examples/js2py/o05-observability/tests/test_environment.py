"""Boundary tests use synthetic values only; never a real external DB or secret."""
import os
import re

import pytest

from ops import cluster
from ops.data import grant_app
from ops.migrate import upgrade
from ops.server import running


# One test with multiple assertions, not a claim of this many pytest cases.
LIBPQ_NAMES = (
    "PGHOST", "PGHOSTADDR", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD",
    "PGPASSFILE", "PGSERVICE", "PGSERVICEFILE", "PGSYSCONFDIR", "PGOPTIONS",
    "PGAPPNAME", "PGCONNECT_TIMEOUT", "PGSSLMODE", "PGSSLCERT", "PGSSLKEY",
    "PGSSLROOTCERT", "PGGSSENCMODE", "PGTARGETSESSIONATTRS", "PGLOADBALANCEHOSTS",
    "PGFUTURE_OVERRIDE",
)


def test_libpq_overrides_rejected_before_creation_or_connection(monkeypatch, tmp_path):
    def forbidden(*args, **kwargs):
        raise AssertionError("Environment guard must run before any allocation or libpq call")

    monkeypatch.setattr(cluster.tempfile, "mkdtemp", forbidden)
    monkeypatch.setattr(cluster.psycopg, "connect", forbidden)
    canary = "synthetic-private-environment-value"
    for name in LIBPQ_NAMES:
        with monkeypatch.context() as change:
            change.setenv(name, canary)
            for action in [lambda: cluster.OwnedCluster().__enter__(),
                           lambda: cluster.connect(tmp_path / "not-a-cluster", "source"),
                           lambda: upgrade(tmp_path / "not-a-cluster", "007_project_description")]:
                with pytest.raises(RuntimeError, match="Refusing inherited PostgreSQL environment") as caught:
                    action()
                assert name in str(caught.value) and canary not in str(caught.value)
            assert os.environ[name] == canary  # Never silently mutate caller settings.


def test_pg_bin_allowed_and_password_file_is_owned(monkeypatch, tmp_path):
    calls = []
    sentinel = object()

    def capture(**kwargs):
        calls.append(kwargs)
        return sentinel

    monkeypatch.setenv("PG_BIN", str(tmp_path / "tool-location-only"))
    monkeypatch.setattr(cluster, "checked_root", lambda value: tmp_path)
    monkeypatch.setattr(cluster.psycopg, "connect", capture)
    cluster.reject_connection_environment()
    assert cluster.connect(tmp_path, "source") is sentinel
    assert calls[0]["host"] == str(tmp_path / "socket")
    assert calls[0]["dbname"] == "source"
    assert calls[0]["user"] == "lab_owner"
    assert calls[0]["passfile"] == str(tmp_path / "empty.pgpass")


def test_two_actual_servers_own_distinct_ephemeral_ports():
    with cluster.OwnedCluster() as owned:
        root = owned.root
        upgrade(root, "007_project_description")
        grant_app(root)
        with running(root, "v2") as first:
            with running(root, "v2") as second:
                ports = {first.base_url.port, second.base_url.port}
                assert len(ports) == 2 and all(0 < port <= 65535 for port in ports)
                assert first.get("/health/ready").status_code == 200
                assert second.get("/health/ready").status_code == 200
                logs = list(root.glob("service-*.log"))
                assert len(logs) == 2
                banner_ports = set()
                for path in logs:
                    match = re.search(r"Uvicorn running on http://127\.0\.0\.1:([0-9]+)", path.read_text())
                    assert match
                    banner_ports.add(int(match.group(1)))
                assert banner_ports == ports
        # Each context also waits for its child and checks the former port is closed.
    assert not root.exists()
