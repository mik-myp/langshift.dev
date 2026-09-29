from datetime import timedelta
import json
import os
import secrets
import stat
import subprocess
import sys
import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from client import read_token, save_token
from models import AuthSession, User
from security import digest_token, hasher, set_active, utc_now


def test_hashes_are_salted_argon2id_and_storage_has_only_digest(api, database, accounts):
    token = api.token("Alice", accounts.password)
    with Session(database) as session:
        alice, bob = [session.get(User, key) for key in (accounts.Alice, accounts.Bob)]
        assert alice.password_hash.startswith("$argon2id$v=19$m=65536,t=3,p=4$")
        assert alice.password_hash != bob.password_hash
        assert hasher.verify(alice.password_hash, accounts.password)
        stored = session.get(AuthSession, digest_token(token))
        assert stored is not None and stored.token_digest != token and stored.auth_version == alice.auth_version
        assert stored.expires_at > stored.issued_at and stored.expires_at.tzinfo is not None
    result = api.request("GET", "/users/me", token=token)
    assert result.status == 200 and set(result.body) == {"id", "login", "is_active"}


def test_wrong_password_and_unknown_account_share_response(api, accounts):
    wrong = secrets.token_urlsafe(24)
    api.secrets.append(wrong)
    first = api.request("POST", "/auth/token", {"login": "Alice", "password": wrong})
    second = api.request("POST", "/auth/token", {"login": "Unknown", "password": wrong})
    assert first.status == second.status == 401 and first.body == second.body
    assert first.headers.get("www-authenticate") == "Bearer"


def test_missing_malformed_and_tampered_bearer(api, accounts):
    token = api.token("Alice", accounts.password)
    replacement = ("A" if token[0] != "A" else "B") + token[1:]
    for value in (None, "bad", token + "x", replacement):
        assert api.request("GET", "/users/me", token=value).status == 401


def test_expiry_is_checked_in_database(api, accounts, database):
    token = api.token("Alice", accounts.password)
    with Session(database) as session, session.begin():
        credential = session.get(AuthSession, digest_token(token))
        credential.issued_at = utc_now() - timedelta(hours=2)
        credential.expires_at = utc_now() - timedelta(hours=1)
    assert api.request("GET", "/users/me", token=token).status == 401


def test_logout_revokes_only_current_session(api, accounts):
    first, second = api.token("Alice", accounts.password), api.token("Alice", accounts.password)
    result = api.request("POST", "/auth/logout", token=first)
    assert result.status == 204 and result.body_bytes == 0
    assert api.request("GET", "/users/me", token=first).status == 401
    assert api.request("GET", "/users/me", token=second).status == 200


def test_logout_all_revokes_old_but_not_new_login(api, accounts):
    first, second = api.token("Alice", accounts.password), api.token("Alice", accounts.password)
    assert api.request("POST", "/auth/logout-all", token=first).status == 204
    assert api.request("GET", "/users/me", token=first).status == 401
    assert api.request("GET", "/users/me", token=second).status == 401
    fresh = api.token("Alice", accounts.password)
    assert api.request("GET", "/users/me", token=fresh).status == 200


def test_change_password_requires_old_password_and_revokes_all(api, accounts):
    first, second = api.token("Alice", accounts.password), api.token("Alice", accounts.password)
    new = secrets.token_urlsafe(24)
    api.secrets.append(new)
    wrong = api.request("POST", "/users/me/password",
        {"current_password": "wrong", "new_password": new}, first)
    assert wrong.status == 401
    assert api.request("GET", "/users/me", token=first).status == 200
    changed = api.request("POST", "/users/me/password",
        {"current_password": accounts.password, "new_password": new}, first)
    assert changed.status == 204 and changed.body_bytes == 0
    assert api.request("GET", "/users/me", token=first).status == 401
    assert api.request("GET", "/users/me", token=second).status == 401
    assert api.request("POST", "/auth/token", {"login": "Alice", "password": accounts.password}).status == 401
    assert api.request("GET", "/users/me", token=api.token("Alice", new)).status == 200


def test_disable_and_reenable_never_revives_old_tokens(api, accounts, database):
    old = api.token("Alice", accounts.password)
    with Session(database) as session, session.begin():
        set_active(session, "Alice", False)
    assert api.request("GET", "/users/me", token=old).status == 401
    assert api.request("POST", "/auth/token", {"login": "Alice", "password": accounts.password}).status == 401
    with Session(database) as session, session.begin():
        set_active(session, "Alice", True)
    assert api.request("GET", "/users/me", token=old).status == 401
    assert api.request("GET", "/users/me", token=api.token("Alice", accounts.password)).status == 200


def test_validation_does_not_echo_secret_input_or_extra_keys(api):
    marker = "SENSITIVE-" + secrets.token_hex(12)
    api.secrets.append(marker)
    for payload in ({"login": "Alice", "password": marker * 20},
                    {"login": "Alice", "password": 42, marker: marker}):
        result = api.request("POST", "/auth/token", payload)
        encoded = json.dumps(result.body)
        assert result.status == 422 and marker not in encoded and '"input"' not in encoded and '"ctx"' not in encoded
    result = api.request("POST", "/auth/token", raw=('{"password":"'+marker).encode())
    assert result.status == 422 and marker not in json.dumps(result.body)


def test_private_client_file_and_no_raw_token_output(tmp_path):
    token = secrets.token_urlsafe(32)
    file = tmp_path / ".session-test.json"
    save_token(file, token)
    assert stat.S_IMODE(file.stat().st_mode) == 0o600 and read_token(file) == token
    file.chmod(0o644)
    with pytest.raises(ValueError):
        read_token(file)


def test_operator_cli_creates_account_without_echo(cluster, database, api):
    password = secrets.token_urlsafe(24)
    api.secrets.append(password)
    result = subprocess.run([sys.executable, "admin.py", "create-user", "OperatorCreated"],
        input=password + "\n" + password + "\n", text=True, capture_output=True,
        env=dict(os.environ, DATABASE_URL=cluster.url()), timeout=15)
    assert result.returncode == 0 and password not in result.stdout + result.stderr
    assert api.request("GET", "/users/me", token=api.token("OperatorCreated", password)).status == 200


def test_failed_configuration_does_not_echo_url(tmp_path):
    marker = "private-" + secrets.token_hex(8)
    result = subprocess.run([sys.executable, "-c", "import db"], text=True, capture_output=True,
        env=dict(os.environ, DATABASE_URL="invalid://" + marker), timeout=10)
    assert result.returncode != 0 and marker not in result.stdout + result.stderr


def test_committed_session_survives_api_and_owned_postgresql_restart(api, accounts, cluster):
    token = api.token("Alice", accounts.password)
    api.restart()
    assert api.request("GET", "/users/me", token=token).status == 200
    cluster.restart()
    assert api.request("GET", "/health/ready").status == 200
    assert api.request("GET", "/users/me", token=token).status == 200


def test_password_change_validation_redacts_all_sensitive_fields(api, accounts):
    token = api.token("Alice", accounts.password)
    marker = "PRIVATE-" + secrets.token_hex(16)
    api.secrets.append(marker)
    for payload in [
        {"current_password": accounts.password, "new_password": marker * 10},
        {"current_password": marker, "new_password": "short", marker: marker},
        {"current_password": {"nested": marker}, "new_password": accounts.password},
    ]:
        result = api.request("POST", "/users/me/password", payload, token)
        encoded = json.dumps(result.body)
        assert result.status == 422
        assert marker not in encoded and accounts.password not in encoded
        assert '"input"' not in encoded and '"ctx"' not in encoded and '"msg"' not in encoded


def test_real_inflight_user_lock_orders_disable_then_future_requests_fail(api, accounts, database, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    import time
    from security import authenticate
    token = api.token("Alice", accounts.password)
    first = Session(database)
    first.begin()
    authenticate(first, "Bearer " + token)
    first_pid = first.scalar(text("SELECT pg_backend_pid()"))
    started, state = threading.Event(), {}
    def disable():
        with Session(database) as second, second.begin():
            second.execute(text("SET LOCAL lock_timeout = '8s'"))
            state["pid"] = second.scalar(text("SELECT pg_backend_pid()"))
            started.set()
            set_active(second, "Alice", False)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(disable)
        try:
            assert started.wait(3)
            blocked = False
            for _ in range(100):
                with database.connect() as observer:
                    blockers = observer.scalar(text("SELECT pg_blocking_pids(:pid)"), {"pid": state["pid"]})
                if first_pid in blockers:
                    blocked = True
                    break
                time.sleep(.02)
            assert blocked and first_pid != state["pid"]
            first.commit()  # This already-authorized operation is ordered before disable.
            future.result(timeout=10)
        finally:
            first.rollback()
            first.close()
    assert api.request("GET", "/users/me", token=token).status == 401
    directory = __import__("pathlib").Path(os.environ.get("SECURITY_EVIDENCE_DIR", str(tmp_path)))
    directory.mkdir(parents=True, exist_ok=True)
    (directory / (database.url.database + "-" + __import__("pathlib").Path.cwd().name + "-disable-race.json")).write_text(
        json.dumps({"prior_request_pid":first_pid,"revocation_pid":state["pid"],"observed_lock_wait":blocked,
                    "post_commit_http":401,"boundary":"already-authorized work may finish before revocation commits"},indent=2))


def test_real_client_login_request_and_password_change_without_echo(api, accounts, tmp_path):
    path = tmp_path / ".session-client.json"
    command = [sys.executable, "client.py", "--port", str(api.port), "--session", str(path)]
    signed_in = subprocess.run(command + ["login", "Alice"], input=accounts.password + "\n",
                               capture_output=True, text=True, timeout=15)
    assert signed_in.returncode == 0 and "HTTP 200" in signed_in.stdout
    token = read_token(path)
    api.secrets.extend([token, accounts.password])
    assert accounts.password not in signed_in.stdout + signed_in.stderr
    assert token not in signed_in.stdout + signed_in.stderr
    result = subprocess.run(command + ["request", "GET", "/users/me"],
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0 and "HTTP 200" in result.stdout
    assert token not in result.stdout + result.stderr
    new = secrets.token_urlsafe(24)
    api.secrets.append(new)
    changed = subprocess.run(command + ["change-password"],
        input=accounts.password + "\n" + new + "\n" + new + "\n",
        capture_output=True, text=True, timeout=15)
    assert changed.returncode == 0 and "HTTP 204" in changed.stdout and not path.exists()
    assert all(value not in changed.stdout + changed.stderr for value in [accounts.password, new, token])
    assert api.request("GET", "/users/me", token=token).status == 401
    assert api.request("GET", "/users/me", token=api.token("Alice", new)).status == 200


def test_database_error_redacted_and_service_recovers(api, accounts, database):
    token = api.token("Alice", accounts.password)
    # A real PostgreSQL error, not a mocked exception or SQLite replacement.
    with database.begin() as connection:
        connection.execute(text("ALTER TABLE auth_sessions RENAME TO unavailable_sessions"))
    try:
        failure = api.request("GET", "/users/me", token=token)
        assert failure.status == 503
        assert failure.body == {"detail": "Service temporarily unavailable"}
    finally:
        with database.begin() as connection:
            connection.execute(text("ALTER TABLE unavailable_sessions RENAME TO auth_sessions"))
    assert api.request("GET", "/users/me", token=token).status == 200


def test_token_response_not_cacheable_and_readiness_checks_revision(api, accounts, database):
    result = api.request("POST", "/auth/token", {"login": "Alice", "password": accounts.password})
    assert result.status == 200 and result.headers["cache-control"] == "no-store"
    with database.begin() as connection:
        revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
        connection.execute(text("UPDATE alembic_version SET version_num='unavailable'"))
    try:
        assert api.request("GET", "/health/live").status == 200
        assert api.request("GET", "/health/ready").status == 503
    finally:
        with database.begin() as connection:
            connection.execute(text("UPDATE alembic_version SET version_num=:version"), {"version": revision})
    assert api.request("GET", "/health/ready").status == 200
