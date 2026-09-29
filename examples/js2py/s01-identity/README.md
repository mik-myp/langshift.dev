# s01-identity: complete standalone local lab

[简体中文](README.zh-cn.md) · [繁體中文](README.zh-tw.md)

## 1. Contract and starting point

This is the standalone download for S01. It imports no other chapter and needs no frontend dependencies. Readers have completed D06's PostgreSQL, transactions, migrations and fixtures; S02 also builds on S01 identity, and S03 on S02 object policy. Predict results before verifying real HTTP and database behavior. Compilation is not API acceptance. The chapter contains full mechanisms and folded answers.

Every API binds to 127.0.0.1; PostgreSQL uses only the helper's private Unix socket. **Never expose this lab publicly or connect to/stop the user's existing database.** Local trust relies on the private directory and local OS-user boundary; it is not a production database-authentication design.

Baseline verified **2026-09-28**: CPython 3.13.15, uv 0.12.13, FastAPI 0.135.1, Uvicorn 0.42.0, Pydantic 2.12.5, SQLAlchemy 2.0.54, Alembic 1.20.0, psycopg[binary] 3.3.6, PostgreSQL 18.6, argon2-cffi 25.1.0, pytest 8.4.2. The real public-PyPI uv.lock pins resolved dependencies, not necessarily the latest. Python is >=3.13,<3.14; uv does not install this lab as a distributable package.

## 2. File responsibilities

| File | Responsibility |
| --- | --- |
| pyproject.toml / uv.lock / .python-version | Declaration, full resolution and interpreter pin |
| migrations / alembic.ini | Actual empty-to-current migration chain; 001–003 retained from D |
| models.py / schemas.py | Separate database, request and public representations |
| db.py / security.py | Per-request transactions, Argon2id and session validation/revocation, not a global Session |
| app.py / serve.py | HTTP adaptation, sanitized errors and loopback-only process entry |
| admin.py / client.py | Controlled provisioning and getpass client; no password/Bearer printing |
| labdb.py | Create, verify ownership, restart and stop a dedicated temporary PG cluster |
| tests / solutions | Real PG/HTTP acceptance and independent variation answers |
| SOURCES.md / VERIFICATION.md | Official review and actual evidence/exclusions |

## 3. Working directory and first start

Use the extracted `s01-identity` root, or `examples/js2py/s01-identity` in the repository. Confirm that PostgreSQL 18.6 postgres, initdb and pg_ctl are available; this verification used /opt/homebrew/bin. An existing service is not a substitute.

```bash
export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
export UV_PYTHON_INSTALL_DIR=/tmp/langshift-js2py-python-20260928
export UV_CACHE_DIR=/tmp/langshift-js2py-uv-cache-20260928
unset VIRTUAL_ENV UV_PROJECT_ENVIRONMENT UV_ACTIVE UV_PYTHON UV_CONFIG_FILE
export UV_NO_CONFIG=true
uv --version
uv sync --locked
uv run --locked python --version
uv run --locked python labdb.py start
```

Expect uv 0.12.13 and Python 3.13.15. labdb.py creates a mode-0700 mkdtemp directory, mode-0600 ownership marker and .lab-state.json, then starts PG without TCP listeners. **Copy its printed DATABASE_URL export line into this terminal.** It names a private socket and contains no password. isolation.py removes implicit PG* configuration before connections; subprocesses also exclude PGHOSTADDR/PGSERVICE and other libpq environment settings. Do not carry an arbitrary preexisting DATABASE_URL into the lab. Then:

```bash
uv run --locked alembic upgrade head
uv run --locked alembic current
uv run --locked python admin.py create-user Alice
uv run --locked python serve.py --port 8061
```

current must report 004_identity. Migration 004 leaves legacy D users disabled without default passwords; provision explicitly. create-user refuses to overwrite a configured password. New passwords are 15–128 characters, entered and confirmed only at getpass prompts, never arguments, logs, default environment values or tutorial constants. Never blindly stamp. Security downgrades intentionally do not delete history automatically.

/health/live checks the process; /health/ready checks database access and the exact revision, not every data invariant. Open another terminal in this directory; the client needs no DATABASE_URL. On an HTTP port conflict, leave existing processes alone and stop your failed command or choose a free port, updating every client command too. Never kill processes globally by name.

## 4. Identity, APIs and field contract

Every package includes POST /auth/token, GET /users/me, POST /users/me/password, POST /auth/logout and /auth/logout-all. Passwords are secret JSON-body values, supplied only through the client's dedicated prompts. The returned random Bearer is kept in a private mode-0600 .session*.json file. Do not cat, screenshot or commit it. The client explicitly disables environment proxies with `ProxyHandler({})`, refuses redirects, and token responses set no-store. A loopback URL alone would not bypass inherited proxy settings. This terminal file is not browser-localStorage advice.

The established argon2-cffi library supplies Argon2id with random salts and m=65536 KiB/t=3/p=4. secrets.token_urlsafe(32) generates tokens; the DB stores only SHA-256 digests, expiry and auth_version. Requests recheck active/revoked/expiry/version state instead of trusting an earlier login. Password change and logout-all increment the version; both disable and enable increment it, so old tokens never revive. Shared user locks and exclusive revocation locks define ordering: an existing operation may finish, and new operations after revocation commits are denied. Already-started responses are not recalled.

## 5. Real-client acceptance

```bash
uv run --locked python client.py --port 8061 --session .session-alice.json login Alice
uv run --locked python client.py --port 8061 --session .session-alice.json request GET /users/me
cp -p .session-alice.json .session-before-change.json
uv run --locked python client.py --port 8061 --session .session-alice.json change-password
uv run --locked python client.py --port 8061 --session .session-before-change.json request GET /users/me
```

```bash
uv run --locked python client.py --port 8061 --session .session-alice.json login Alice
uv run --locked python client.py --port 8061 --session .session-alice.json request POST /auth/logout-all
uv run --locked python client.py --port 8061 --session .session-alice.json request GET /users/me
```

Expect login200→me200→password change204/empty body→old copy401; new-password login200→logout-all204→old token401. The client removes its current private file after password change, but the database version change is the real invalidation. Log in into two different files to prove single-session logout leaves the other valid. After disable, login and old sessions fail401; enable does not revive the old token, but fresh login succeeds200. Unknown accounts and incorrect passwords share the same401; malformed input gets sanitized422. Never put credentials in acceptance notes.

## 6. Automated acceptance and failure recovery

```bash
uv run --locked python -m pytest -q
```

Currently 22 cases. Fixtures ignore incoming DATABASE_URL, create owned PG18.6, migrate, start real Uvicorn and send real standard-library HTTP. Each test clears only declared tables in its owned DB. The solution entry app is exercised along with all base routes. VERIFICATION.md records counts and redacted evidence. Maintainers can set SECURITY_EVIDENCE_DIR to retain redacted HTTP/two-connection observations; those are not production audit logs.

| Failure | Observation and recovery |
| --- | --- |
| Missing/invalid DATABASE_URL | No actual connection string in the error; recopy this lab's labdb.py status export |
| ready503, live200 | Check owned PG and migration state; repair to get ready200, never skip migration |
| Incorrect/expired/altered Bearer | Generic401; log in through the dedicated client, do not bypass checks in DB |
| Invalid password/JSON/extra field | 422 only loc/type; no input/ctx/msg or secret field-name echo; correct the input |
| Actual DB operation error | Generic409/503, transaction rollback; repair schema and later request succeeds; no driver detail |
| HTTP port already occupied | Leave the existing process alone; change only your server/client port |

Tests really expire sessions, alter token characters, disable/reenable accounts, change passwords, and restart the API/owned PG. Sensitive fields, extra keys and malformed JSON are checked in responses and application/PG logs. S02/S03 add body/query/path probes, and revocation races have distinct backend PIDs plus pg_blocking_pids evidence. This does not prove every unknown exception, third-party logger, proxy or APM sanitized. New paths require independent security review.

The client-isolation regression uses only owned loopback listeners and synthetic credentials: proxy variables are present, no_proxy is absent, target receives three requests, proxy receives zero and redirect target receives zero. A separate helper test injects invalid PGHOSTADDR/PGSERVICE/PGUSER/PGDATABASE/PGPASSWORD settings, then starts, restarts and removes an owned socket-only cluster successfully.

For maintainer clean-copy runs, the repository runner supports `--lab-root /path/to/extracted-lab` or `JS2PY_LAB_ROOT` (also a parent of the named lab directories). It clears inherited VIRTUAL_ENV, UV_PROJECT_ENVIRONMENT, UV_ACTIVE, UV_PYTHON and other UV configuration redirects, sets UV_NO_CONFIG, pins Python on the command line, and preserves only the explicit UV_PYTHON_INSTALL_DIR/UV_CACHE_DIR storage paths. It also excludes PG* and pytest plugin/argument overrides. The source-tree default only uses that lab’s own .venv, refusing an environment symlink.

## 7. Independent rebuild and variation
Bring only environment/migrations into a new directory; do not import the reference app. Reimplement models, passwords, session checks/revocation and controlled provisioning. Verify wrong/expired/altered credentials, changes, disabling, both revocations, real restarts and redaction. Add active-session count: two logins=2, revoke one=1, revoke all then log in=1. Exclude Bob, old versions, expired/revoked rows; never return digests. Implement first, then consult solutions/session_count.py.
```bash
uv run --locked python serve.py --port 8061 --app solutions.session_count:app
uv run --locked python client.py --port 8061 --session .session-alice.json request GET /users/me/session-count
```

## 8. Pause, resume and final cleanup

First Ctrl-C in the terminal owning the API. To retain data, use labdb.py status and save only nonsecret state notes. On resumption copy its export and start the API. Use restart to check persistence; do not call deletion by stop a persistence failure.

```bash
uv run --locked python labdb.py status
uv run --locked python labdb.py restart
```

After API/PG restart, committed records and still-valid unrevoked sessions remain. A session may naturally reach its TTL and return401; that does not mean the database disappeared. When finished, stop the API before:

```bash
uv run --locked python labdb.py stop
```

**After verifying ownership and server exit, stop deletes the entire temporary PG data directory.** Remove only private .session files you created, without broad filesystem globs or stopping the user's DB.

```text
checkpoint: s01-identity
migration: 004_identity
last_result: record status and non-secret object IDs only
credential_values: never recorded
api: stopped in owning terminal
postgres: retained for resume OR explicitly deleted by owned helper
next: status, export, migrate if needed, serve, fresh login if expired
```

## 9. Packaging and unverified boundaries

The sibling `s01-identity-files.json` is the positive allowlist: packaging reads only those paths, never recursively archives the lab directory. Exclude .venv, __pycache__, .pytest_cache, .env*, .lab-state.json, .session* (including interrupted .new files), PGdata/socket, logs, credentials and temporary evidence. Integration builds the archive; this package contains no runtime environment or database.

Unverified: production TLS, throttling/capacity, body-size limits, compromised-password checks, recovery/MFA, external logging/APM, arbitrary unknown exceptions, clock skew, backups/restores, RLS, cross-service effects and every lock interleaving. Global lists/already-started responses cannot be retroactively revoked; concurrent invitation and target disabling is not an atomic-onboarding promise. S03 also makes no perpetual-after-purge deduplication, exactly-once or unconditional retry guarantee. Passing tests is not passing a security audit; integration will independently review final file hashes.
