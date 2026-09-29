"""Environment boundary regressions; no default/remote database is contacted.

Negative unit cases replace psycopg/process entry points before adding poison.
Integration cases use only the already-owned private cluster and a listener we
bind ourselves on loopback; this module never starts another database target.
"""
import json
import os
from pathlib import Path
import select
import shutil
import socket
import stat
import subprocess
import sys
from unittest.mock import Mock

import pytest
from psycopg.conninfo import conninfo_to_dict

import labctl


@pytest.fixture(autouse=True)
def fresh_owned_database(monkeypatch):
    # Override the business suite's autouse reset: negative cases must reach NO
    # SQL at all. Real integration cases below explicitly use the owned cluster.
    for name in tuple(os.environ):
        if name.startswith("PG") and name not in {"PGHOST", "PG_BIN"}:
            monkeypatch.delenv(name)


@pytest.mark.parametrize("name", [
    "PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE", "PGSYSCONFDIR", "PGPASSFILE",
    "PGPASSWORD", "PGUSER", "PGDATABASE", "PGPORT", "PGOPTIONS",
    "PGCONNECT_TIMEOUT", "PGAPPNAME", "PGCLIENTENCODING", "PGSSLMODE",
    "PGSSLKEY", "PGSSLCERT", "PGSSLROOTCERT", "PGREQUIRESSL", "PGREQUIREAUTH",
    "PGGSSENCMODE", "PGTARGETSESSIONATTRS", "PGLOADBALANCEHOSTS", "PGDATA",
    "PG_FUTURE_DEFAULT",
])
def test_reject_before_state_sql_or_subprocess(monkeypatch, name):
    sql = Mock(side_effect=AssertionError("must not reach psycopg"))
    process = Mock(side_effect=AssertionError("must not launch a process"))
    state = Mock(side_effect=AssertionError("must not load state"))
    monkeypatch.setattr(labctl.psycopg, "connect", sql)
    monkeypatch.setattr(labctl.subprocess, "run", process)
    monkeypatch.setattr(labctl, "load_state", state)
    monkeypatch.setenv(name, "synthetic-secret-not-to-be-printed")
    with pytest.raises(RuntimeError) as error:
        labctl.connect()
    assert str(error.value) == "Refusing implicit PostgreSQL environment: " + name
    sql.assert_not_called()
    process.assert_not_called()
    state.assert_not_called()


def test_empty_setting_is_still_rejected(monkeypatch):
    monkeypatch.setenv("PGSERVICE", "")
    with pytest.raises(RuntimeError, match="environment: PGSERVICE$"):
        labctl.check_environment()


def test_error_lists_only_sorted_names(monkeypatch):
    monkeypatch.setenv("PGSERVICE", "service-secret")
    monkeypatch.setenv("PGPASSWORD", "password-secret")
    with pytest.raises(RuntimeError) as error:
        labctl.check_environment()
    assert str(error.value) == (
        "Refusing implicit PostgreSQL environment: PGPASSWORD, PGSERVICE"
    )


@pytest.mark.parametrize("entry", [
    "start", "reset", "raw_dsn", "verify_server", "cli-start", "cli-dsn",
    "cli-reset", "cli-psql",
])
def test_all_sql_entries_reject_before_work(monkeypatch, entry):
    sql = Mock(side_effect=AssertionError("must not reach psycopg"))
    process = Mock(side_effect=AssertionError("must not launch a process"))
    state = Mock(side_effect=AssertionError("must not load state"))
    monkeypatch.setattr(labctl.psycopg, "connect", sql)
    monkeypatch.setattr(labctl.subprocess, "run", process)
    monkeypatch.setattr(labctl, "load_state", state)
    monkeypatch.setenv("PGHOSTADDR", "synthetic-not-an-address")
    with pytest.raises(RuntimeError, match="environment: PGHOSTADDR$"):
        if entry.startswith("cli-"):
            monkeypatch.setattr(sys, "argv", ["labctl.py", entry[4:], "--yes-reset"])
            labctl.main()
        elif entry in {"raw_dsn", "verify_server"}:
            getattr(labctl, entry)({})
        else:
            getattr(labctl, entry)()
    sql.assert_not_called()
    process.assert_not_called()
    state.assert_not_called()


def test_run_removes_all_pg_defaults_without_mutating_parent(monkeypatch):
    for name in ("PGHOST", "PG_BIN", "PGHOSTADDR", "PGSERVICE", "PGPASSWORD"):
        monkeypatch.setenv(name, "synthetic-child-poison")
    monkeypatch.setenv("DATABASE_URL", "synthetic-url")
    before = dict(os.environ)
    process = Mock(return_value=subprocess.CompletedProcess([], 0, "", ""))
    monkeypatch.setattr(labctl.subprocess, "run", process)
    labctl.run("explicit-tool", "--version")
    assert process.call_args.kwargs["env"] == {
        k: v for k, v in before.items() if not k.startswith("PG") and k != "DATABASE_URL"
    }
    assert dict(os.environ) == before


def test_psql_has_clean_environment_explicit_passfile_and_no_prompt(monkeypatch, tmp_path):
    state = {"root": str(tmp_path), "port": 50000, "admin": "test_admin",
             "pg_bin": "/synthetic-tools"}
    monkeypatch.setattr(labctl, "load_state", lambda: state)
    monkeypatch.setattr(labctl, "verify_server", lambda state: None)
    monkeypatch.setenv("PGHOST", "/nonexistent/langshift-test-ignore-environment")
    monkeypatch.setenv("DATABASE_URL", "synthetic-url")
    process = Mock(return_value=subprocess.CompletedProcess([], 0))
    monkeypatch.setattr(labctl.subprocess, "run", process)
    monkeypatch.setattr(sys, "argv", ["labctl.py", "psql"])
    labctl.main()
    command = process.call_args.args[0]
    assert command[:3] == ["/synthetic-tools/psql", "-X", "-w"]
    params = conninfo_to_dict(command[3])
    assert params["host"] == str(tmp_path / "socket")
    assert params["passfile"] == str(tmp_path / "empty.pgpass")
    env = process.call_args.kwargs["env"]
    assert not any(k.startswith("PG") or k == "DATABASE_URL" for k in env)


def test_both_dsns_use_private_empty_passfile(tmp_path):
    state = {"root": str(tmp_path), "port": 50000, "admin": "random_test_admin"}
    for admin in (False, True):
        params = conninfo_to_dict(labctl.raw_dsn(state, admin=admin))
        path = Path(params["passfile"])
        assert path == tmp_path / "empty.pgpass"
        assert path.read_bytes() == b""
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert path.stat().st_uid == os.getuid()
        assert params["user"] == (state["admin"] if admin else "lab_student")


@pytest.mark.parametrize("kind", ["symlink", "nonempty", "wide-mode", "directory", "fifo"])
def test_unsafe_passfile_is_refused_before_psycopg(monkeypatch, tmp_path, kind):
    path = tmp_path / "empty.pgpass"
    if kind == "symlink":
        target = tmp_path / "do-not-read"
        target.write_text("synthetic-secret")
        path.symlink_to(target)
    elif kind == "directory":
        path.mkdir()
    elif kind == "fifo":
        os.mkfifo(path, 0o600)
    else:
        path.write_text("synthetic-secret" if kind == "nonempty" else "")
        path.chmod(0o644 if kind == "wide-mode" else 0o600)
    state = {"root": str(tmp_path), "port": 50000, "admin": "test_admin"}
    monkeypatch.setattr(labctl, "load_state", lambda: state)
    sql = Mock(side_effect=AssertionError("must not reach psycopg"))
    monkeypatch.setattr(labctl.psycopg, "connect", sql)
    with pytest.raises((RuntimeError, OSError)):
        labctl.connect()
    sql.assert_not_called()


@pytest.fixture
def owned_listener():
    # Match the private socket's port to catch a regressed PGHOSTADDR override.
    # If this loopback port is occupied, fail safely rather than contact it.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", int(labctl.load_state()["port"])))
        listener.listen(8)
        try:
            yield listener
        finally:
            assert not select.select([listener], [], [], 0.05)[0], (
                "unexpected connection to our loopback listener"
            )


def poisoned_env(tmp_path, listener):
    port = listener.getsockname()[1]
    secret = "synthetic-pass-canary"
    passfile = tmp_path / "supplied.pgpass"
    passfile.write_text(f"*:*:*:*:{secret}\n")
    passfile.chmod(0o600)
    servicefile = tmp_path / "supplied-services.conf"
    servicefile.write_text(
        f"[synthetic_service_canary]\nhostaddr=127.0.0.1\nport={port}\n"
        f"dbname=canary\nuser=canary\npassfile={passfile}\n"
    )
    return dict(os.environ, PG_BIN="/nonexistent/synthetic-tools",
                PGHOST="/nonexistent/langshift-test-ignore-environment",
                PGHOSTADDR="127.0.0.1", PGSERVICE="synthetic_service_canary",
                PGSERVICEFILE=str(servicefile), PGPASSFILE=str(passfile),
                PGPASSWORD=secret, PGOPTIONS="synthetic-options-canary")


def cli(*args, env=None, cwd=None):
    return subprocess.run([sys.executable, "labctl.py", *args],
                          cwd=cwd or labctl.LAB, env=env, text=True,
                          capture_output=True, timeout=40)


@pytest.mark.parametrize("command", ["start", "dsn", "reset", "psql"])
def test_direct_cli_rejects_poison_without_contacting_listener(tmp_path, owned_listener, command):
    env = poisoned_env(tmp_path, owned_listener)
    result = cli(command, "--yes-reset", env=env)
    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "Refusing implicit PostgreSQL environment:" in output
    for name in ("PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE", "PGPASSFILE", "PGPASSWORD"):
        assert name in output
    for value in (env["PGPASSWORD"], env["PGSERVICE"], env["PGSERVICEFILE"], env["PGPASSFILE"]):
        assert value not in output


def test_fresh_standalone_start_rejects_before_creating_state(tmp_path, owned_listener):
    fresh = tmp_path / "fresh"
    fresh.mkdir()
    shutil.copy2(labctl.LAB / "labctl.py", fresh / "labctl.py")
    result = cli("start", env=poisoned_env(tmp_path, owned_listener), cwd=fresh)
    assert result.returncode != 0
    assert "Refusing implicit PostgreSQL environment:" in result.stderr
    assert not (fresh / ".lab-state.json").exists()


def test_ignored_host_url_and_default_pgpass_with_real_private_connections(monkeypatch, tmp_path, owned_listener):
    home = tmp_path / "synthetic-home"
    home.mkdir()
    (home / ".pgpass").write_text("*:*:*:*:synthetic-home-password\n")
    (home / ".pgpass").chmod(0o600)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("PGHOST", "/nonexistent/langshift-test-ignore-environment")
    monkeypatch.setenv("DATABASE_URL", f"postgresql://127.0.0.1:{owned_listener.getsockname()[1]}/canary")
    state = labctl.load_state()
    with labctl.connect(autocommit=True) as conn:
        assert conn.execute("SELECT current_database(), current_user").fetchone() == (
            "langshift_lab", "lab_student"
        )
        assert conn.info.host == str(Path(state["root"]) / "socket")
        # PQpass exposes the selected password, even when trust didn't need it.
        assert conn.pgconn.password == b""
    query = tmp_path / "private-query.sql"
    query.write_text("SELECT current_database(), current_user;\n")
    result = cli("psql", "--file", str(query), env=dict(os.environ))
    assert result.returncode == 0, result.stderr
    assert "langshift_lab" in result.stdout and "lab_student" in result.stdout
    assert "synthetic-home-password" not in result.stdout + result.stderr
    assert (home / ".pgpass").read_text() == "*:*:*:*:synthetic-home-password\n"


def test_poisoned_status_stop_and_restart_recovery(tmp_path, owned_listener):
    env = poisoned_env(tmp_path, owned_listener)
    state_before = labctl.load_state()
    try:
        running = cli("status", env=env)
        assert running.returncode == 0, running.stderr
        assert json.loads(running.stdout)["running"] is True
        stopped = cli("stop", env=env)
        assert stopped.returncode == 0, stopped.stderr
        status = cli("status", env=env)
        assert status.returncode == 0, status.stderr
        assert json.loads(status.stdout)["pg_ctl_status"] == 3
        assert cli("stop", env=env).returncode == 0  # Idempotent cleanup.
        refused_restart = cli("start", env=env)
        assert refused_restart.returncode != 0
        assert "Refusing implicit PostgreSQL environment:" in refused_restart.stderr
        assert json.loads(cli("status", env=env).stdout)["running"] is False
    finally:
        # Restore only this marker-checked cluster for the remaining tests.
        restored = cli("start", env=dict(os.environ))
        assert restored.returncode == 0, restored.stderr
    assert labctl.load_state() == state_before


def test_stop_keeps_identity_failure_as_a_hard_boundary(monkeypatch, tmp_path):
    state = {"root": str(tmp_path), "pg_bin": "/saved-private-tools"}
    monkeypatch.setattr(labctl, "load_state", lambda: state)
    monkeypatch.setattr(labctl, "check_pid_file", lambda state: None)
    monkeypatch.setenv("PGHOSTADDR", "synthetic-not-an-address")
    calls = []

    def fake_run(*args, **kwargs):
        calls.append(args)
        if args[0] == sys.executable:
            raise RuntimeError("synthetic server identity mismatch")
        assert args[-1] == "status"
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(labctl, "run", fake_run)
    with pytest.raises(RuntimeError, match="synthetic server identity mismatch"):
        labctl.stop()
    assert len(calls) == 2
    assert calls[0][0] == "/saved-private-tools/pg_ctl"
    assert calls[1] == (sys.executable, str(labctl.LAB / "labctl.py"), "dsn")
    assert not any("stop" in args for args in calls)
