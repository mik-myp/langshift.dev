# Restore verification and controlled reopening — o06-recovery

Complete independent local lab. Read the matching O04/O05/O06 lesson before running.
No other chapter directory is imported. The sibling `o06-recovery-files.json` is the
explicit download/source allowlist; do not recursively ZIP the live directory.

## Tested environment and commands

Date: 2026-09-28. CPython3.13.15, uv0.12.13, pytest8.4.2, FastAPI0.135.1,
Uvicorn0.42.0, Pydantic2.12.5, HTTPX0.28.1, SQLAlchemy2.0.54, Alembic1.20.0,
psycopg[binary]3.3.6, PostgreSQL18.6, Argon2-cffi25.1.0. Starlette0.52.1 and
AnyIO4.12.1 are fixed for compatibility. Requires Python >=3.13,<3.14 and
uv package=false. The actual lock uses public PyPI with artifact hashes.

Run from this extracted directory. PostgreSQL tools postgres/initdb/pg_ctl/psql/
pg_dump/pg_restore must ALREADY be available at /opt/homebrew/bin or an explicit
PG_BIN directory. This lab does not install a system server. An incorrect version
is rejected before modifying a database. Alternative systems require their own
runtime verification, not a claim that macOS evidence covers Linux.

The repository runner reconstructs child settings: inherited `UV_*`, virtual-environment selectors, and Python injection settings are removed before the course cache/interpreter directories, public PyPI, and `UV_NO_CONFIG=1` are set. Only `PG_BIN` survives the `PG*` filter. A real check uses an owned external-venv decoy, a nonexistent interpreter, and invalid user uv configuration: installation must stay inside the clean copy's `.venv`, with the decoy unchanged. This cannot undo actions an outer uv command already performed before Python started. Before the manual uv commands below, leave other virtual environments and use a clean terminal; remove overrides such as `VIRTUAL_ENV`, `UV_PROJECT_ENVIRONMENT`, `UV_ACTIVE`, `UV_PYTHON`, and `UV_CONFIG_FILE`, and set `UV_NO_CONFIG=1`. If a direct Python entry rejects PG settings, remove only the reported names from this experiment's environment; never edit production configuration or print their values.

```bash
uv sync --locked
uv run --locked python ci.py
uv run --locked python -m pytest -q solutions
uv run --locked python demo.py
```

ci.py runs syntax checks, 6 ordinary tests and the real subprocess/database
drill. The independent solutions add 1 test(s). demo.py is already part
of ci.py; running it separately replays the drill from a fresh cluster. Stable
PASS lines indicate checked stages; durations are measured, not fixed outputs.
No syntax check, mocked decision or YAML inspection replaces these runtime checks.

## What this particular lab proves

Three restore-focused tests use real PostgreSQL to check actual import, corrupt-file rejection, and refusal to overwrite a target. The drill creates
a custom pg_dump archive, verifies inventory/checksum, restores into a NEW isolated
database, compares all table fingerprints, and tests constraints, identity
sequences and runtime privileges. A truncated copy is rejected by checksum AND
an actual failing pg_restore invocation; its target has no user tables.

A snapshot can revive revoked tokens or old membership. Before granting runtime
CONNECT, the restored accounts are disabled, auth_version incremented, and
sessions removed. The synthetic post-backup security ledger is reconciled and
only reviewed fixture accounts are enabled. Real HTTP checks reject old/expired
tokens and cross-user reads. Without authoritative newer security records, keep
real accounts disabled and the target isolated; a backup is not current authority.

The source retains one deliberately committed post-snapshot task absent from the
restore. MEASURED reports observed snapshot age and restore-plus-validation time,
not promised production RPO/RTO. Roles/globals/configuration/keys/external files
are not magically included in pg_dump. Both databases share one owned host;
cross-host disaster recovery, scheduled/encrypted/off-site retention and PITR are
not tested. All synthetic archives are mode0600 under mode0700 and deleted on exit.
The independent manifest gate is NOT a substitute for a successful real restore.

## Environment boundaries and port ownership

Passing a private-socket host is not sufficient by itself: libpq can still obtain other connection defaults from `PGHOSTADDR`, `PGSERVICE`, `PGSERVICEFILE`, and related variables. `reject_connection_environment` rejects every inherited `PG*` name before temporary-directory creation and before each direct connection, migration, or server launch. The only exception is `PG_BIN`, which locates executables, not a database. Errors list names only, never their values, and do not mutate the caller's environment. Python connections, SQLAlchemy's connection creator, and PostgreSQL subprocesses use an empty mode0600 `empty.pgpass` in the owned directory rather than the user's default password file. Direct `demo.py` and `ci.py` execution have these guards too; safety does not depend on the repository runner cleaning up first.

The controller no longer probes an unused port, closes that socket, and asks another process to acquire the same number. Uvicorn binds `--port 0` itself. The controller reads the actual port from **that child's own private startup log**, then requests readiness. `--no-access-log` does not suppress the info-level startup banner; the controller explicitly selects uncolored logs and one worker. Concurrent identical releases have distinct log files. A real test starts two servers together and checks their different ports, corresponding banners, actual requests, and cleanup. This removes the probe-close-rebind window, not every possible concurrency failure. A future incompatible Uvicorn banner format fails by deadline rather than guessing a port.

`tests/test_environment.py` adds three cases: inherited PG defaults are rejected before allocation/connection; `PG_BIN` and the owned empty password file have explicit boundaries; and two real services each bind port0, pass HTTP checks, and exit cleanly. The PG variable matrix is multiple assertions in one test, not that many pytest cases.

## Safety, identities and complete source

ops/cluster.py only creates its own mkdtemp /tmp/ls-ops-* cluster. It checks UID,
mode0700, an ownership nonce and symlinks before stopping/deleting. It never accepts
an ambient DATABASE_URL or controls a user PostgreSQL service. A private mode0700
Unix socket with local trust is used only for disposable local teaching; no TCP
PostgreSQL listener is started. Same-OS-user access remains a trust boundary, not
production authentication. The API binds 127.0.0.1 on an owned ephemeral port.

ops/app.py is a limited protected-project operations slice, not the full capstone.
It preserves D/S fields (status/description/priority, not H done/note), checks opaque
Bearer token digest/expiry/revocation/active/auth_version on every request, and
returns 404 for inaccessible projects. Operator fixtures create synthetic users,
sessions and a nonempty idempotency receipt; there is no public login/provisioning
bypass. The complete S03 application must still be integrated before any launch.

SQL revisions001..006 independently reproduce the D/S contract snapshot; 007 adds
nullable projects.description. They are for this disposable laboratory, NOT
permission to replace an existing application's migration history. Application
startup reads schema compatibility but NEVER migrates. Administrative migration
and runtime roles are separate; grants.sql lists the current lab privileges, not a proven minimal set.
The migration controller is serial, not a distributed deployment lock.

This lab verifies separation of administrative and runtime identities and rejection of the tested ALTER/DROP operations; it does **not** prove least-privilege DML. The shared `sql/grants.sql` still gives SELECT/INSERT/UPDATE/DELETE on projects, project_members and tasks, plus USAGE/SELECT on all public sequences. Several grants exceed the current read/create-project routes. Before a real deployment, map each route and job to its table operation, narrow the table/sequence grants, and verify required actions succeed while unused UPDATE/DELETE and other unneeded actions are denied. Passing the existing DDL-denial tests cannot replace that audit.

ops/server.py owns actual Uvicorn subprocesses, waits for database-backed readiness,
and closes only those processes in finally. All database roots, synthetic backups,
private logs and sockets are removed on normal/exceptional exit. Stop/ownership
check failure deliberately refuses unsafe deletion rather than targeting another
service. If interrupted abnormally, investigate only the root owned by your run;
never use global killall, database DROP on an external URL, Docker prune, or broad
filesystem deletion. No real credentials or real user data belong in these labs.

## Failure diagnosis and recovery

Wrong PG version/missing executable: fix the tool path, not the safety check.
Ownership rejection: start a fresh run; do not relabel a user directory. Expected
migration, permission and corruption failures are asserted in the drill, followed
by specific repair and revalidation. Unexpected nonzero exit stops the gate; do
not ignore it or publish an artifact anyway. Raw exceptions/URLs/environment dumps
can contain secrets and are not a safe diagnostic strategy.

Pause record: working directory, lock hash/tool versions, last completed stage,
actual test count, deliberate versus unexpected fault, compatibility/recovery
state, private log/backup policy, owned-process/directory cleanup, unverified
external gates and next action. Normal exit removes temporary state, so resume
with a fresh run. Do not assume a deleted socket or token file still exists.

## Explicitly pending external gates

Actual execution here is macOS arm64 local PG18.6 and loopback HTTP only. No real
Linux/systemd, Docker build/run, Caddy/public reverse proxy, domain/DNS/public TLS,
hosted CI, image publication, production data migration, public traffic switch,
notification delivery, scheduled encrypted/off-site backup, cross-host restore,
representative load test or invited-user trial was performed. These require
separate environments and approvals. Never equate YAML with a release, an alert
return value with delivered notification, or an archive file with recovery.

Full S03 auth/authorization, body-size bounds, measured password-hash capacity,
login throttling, trusted proxy/CORS/credential policy and the O01-O03 external
gates remain prerequisites for an actual launch. Do not expand into public signup.
No Git commit/push, infrastructure purchase or deployment is part of this exercise.

## Packaging and sources

Include only allowlisted source, SQL, configuration, lock and documentation.
Exclude .venv, __pycache__, .pytest_cache, .env/.env.*, credentials, logs, backups,
PostgreSQL data/socket directories and generated runtime manifests. See SOURCES.md
for official references checked live on 2026-09-28. The optional repository-level
scripts/test-js2py-operations-delivery.py verifies clean allowlist copies and the
real drills; it is a maintainer gate, not a substitute for missing external gates.
