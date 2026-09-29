# d03-transactions — Transactions, recovery and real concurrency

Verified 2026-09-28. A standalone lab using real PostgreSQL, not SQLite or browser Python. The full three-language lesson is `module-23-transactions`.

## Outcome and prerequisites

Prerequisites: L00–L14 and H01–H06; D02 additionally requires D01, D03 requires D02. D01 does not assume SQL or operations knowledge. Read the lesson's mechanisms before following this reproducibility guide; installation alone is not mastery.

This lab verifies transactions, recovery and real concurrency. `model-contract.json` records `d01-d03-v1`, and `sql/schema.sql` is the executable DDL. User fixtures are not login accounts. H's done explicitly becomes status (todo/doing/done), note becomes nullable description, and nonnegative estimate minutes is retained. Users, projects, memberships and time fields are new. No existing in-memory data is automatically migrated.

## Fixed environment, no system service installation

- PostgreSQL 18.6 (Homebrew here; actual server_version_num=180006), officially released 2026-08-13.
- CPython 3.13.15, uv 0.12.13, pytest 8.4.2, psycopg[binary] 3.3.6.
- requires-python >=3.13,<3.14; uv package=false; a real public-PyPI uv.lock.
- Only macOS/Homebrew execution was tested. Other OS installation, TCP/TLS and production configuration were not. No Docker, ORM, authentication or frontend dependencies.

Work inside extracted `d03-transactions`, not its parent. Tools already exist on this machine. **Do not run brew services, connect to default port 5432, or initialize existing storage.**

```bash
export PATH="$HOME/.local/bin:$PATH"
export UV_PYTHON_INSTALL_DIR=/tmp/langshift-js2py-python-20260928
export UV_CACHE_DIR=/tmp/langshift-js2py-uv-cache-20260928
export PG_BIN=/opt/homebrew/bin
"$PG_BIN/postgres" --version
"$PG_BIN/initdb" --version
"$PG_BIN/pg_ctl" --version
"$PG_BIN/psql" --version
uv --version
uv sync --locked
uv run --locked python --version
```

Stop on a version mismatch. PG_BIN is a binary directory. psql is the client, postgres the server, initdb creates new storage, and pg_ctl manages the explicitly selected data directory's process. Installed binaries, running processes and data directories are different objects.

## Own an isolated cluster and database

```bash
uv run --locked python labctl.py start
uv run --locked python labctl.py status
uv run --locked python labctl.py dsn
uv run --locked python labctl.py reset --yes-reset
```

Start allocates a short `/tmp/lsdb-*` path (possibly displayed as /private/tmp on macOS), sets root/socket permissions to 0700, saves matching state and marker files, initializes new storage, disables TCP, chooses a private-socket port, and starts pg_ctl with explicit -D and server.log. A random administrator creates database langshift_lab and ordinary role lab_student. A database is a logical namespace inside the cluster; a role is a database identity, not a users-table record. The socket is an endpoint, a DSN describes the address/options, and a connection is an active session.

Passwordless local trust is for the private directory with TCP disabled only. Processes under the same OS account and root are not isolated. Never copy this policy into an exposed or production server. Ownership is checked before connection/reset/stop; SQL connections additionally verify server data directory, system identifier and version. DATABASE_URL is ignored and arbitrary remote DSNs are not accepted. Do not remove those protections.

Reset **destructively recreates the four owned lab tables**, printing `schema + seed ready: users=2 projects=3 members=4 tasks=5`. Every business pytest case and D03 demo scenario also resets. Do not run competing runners or keep business data here. Stop/start retains committed data; OS cleanup of /tmp means this is still neither permanent storage nor backup.

## PostgreSQL environment boundary

`labctl.py` itself checks the environment before startup or any SQL connection, including direct Python imports: **all `PG*` variables except `PG_BIN` and `PGHOST` are rejected**, even empty or unknown names. This deliberately also rejects explicitly overridden variables such as `PGPORT`, `PGUSER` and `PGDATABASE`, not just `PGHOSTADDR`, `PGSERVICE`, `PGSERVICEFILE`, `PGPASSFILE`, `PGPASSWORD` or `PGOPTIONS`. Errors list variable **names only**, never their values. Unset the reported variables in your lab shell before starting or running SQL; do not copy service settings or credentials into this lab.

`PG_BIN` still selects the tool directory. `PGHOST` remains accepted but ignored because every DSN explicitly selects the owned private socket; the maintenance runner's `PGHOST=/nonexistent/...` check remains valid. `DATABASE_URL` is still ignored. All child processes (including initdb, pg_ctl and psql) receive an environment without any `PG*` variables or `DATABASE_URL`; tool paths and data paths are explicit. Python connections do not temporarily mutate the process environment, so D03's concurrent connections do not race over environment restoration.

Every administrator/student DSN explicitly selects the owned root's **empty, mode-0600 `empty.pgpass`**, not the user's default `~/.pgpass`. It is created for new or previously owned clusters; symlink, nonempty, wrong-owner, nonregular or wrong-mode files are refused. psql also uses `-X -w` (no startup file or password prompt). The random administrator and server data-directory/system-identifier/version checks are retained; no business SQL is changed.

**Bad connection environment does not block cleanup:** `status` uses clean pg_ctl calls, and `stop` performs the same server identity check in a clean Python child before stopping the explicitly owned data directory. It does not bypass marker/PID/identity failures. After stopping, remove the reported variables before restarting. An exported `dsn` is descriptive, not a sandbox: do not pass it to an arbitrary client with inherited connection defaults; use `labctl.py psql` instead.

`tests/test_environment.py` adds 50 cases: pre-connection/pre-start mock refusals, subprocess environment checks, passfile checks, standalone CLI refusals against our own loopback listener, private-socket PGHOST/DATABASE_URL compatibility, and poisoned-environment stop/status/restart recovery. These cases override the business tests' automatic SQL reset so negative tests do not open a connection first. They exercise selected failure paths, not every possible attack; same-OS-user/root process or file tampering is outside this lab's isolation boundary.

## Execute, interpret and verify

```bash
uv run --locked python labctl.py psql --file sql/failed_transaction.sql
uv run --locked python demo.py
uv run --locked pytest -q
```

Expect **63 passed** (13 existing business cases + 50 environment cases), with variable duration. ERROR output in intentionally failing SQL is expected; unexpected command failure must not be ignored. D01 checks duplicate 23505, bad foreign key 23503, CHECK 23514, NULL 23502, length 22001 and this version's delete RESTRICT 23001. D02 stores attack payloads literally without dropping tasks, and rejects invalid sorting/pagination in Python. D03 checks second-step 23503, subsequent-query 25P02, zero residue after rollback, real read-committed [30,40], repeatable-read [30,30], lost update 37, atomic increments 42, a one-row uniqueness race, lock timeout 55P03, and old-snapshot update 40001 followed by a whole-unit retry to 42.

The lesson contains exact demo output. D02's fixed ID requires reset first; D03 resets each scenario itself. These tests are execution, not compilation: an actual server applies constraints, parameters, transactions and locks. Independent exercise references are in answers; attempt them before looking. They are not extra baseline schema or HTTP integration.

## File responsibilities

- labctl.py: exclusive startup, address/identity checks, reset, psql and stop; no global service management.
- sql/schema.sql and sql/seed.sql: identical three-lab schema and deterministic fixture; model-contract records the DDL hash.
- sql/*.sql: queries or explicitly labeled failure experiments.
- tests/ and conftest.py: reset only the owned database per business case, including reference-variation execution.
- answers/: references for independent work, not the starting point.
- pyproject.toml, uv.lock, .python-version, .env.example: dependencies/configuration; env.example is documentation, not automatically loaded.
- Three READMEs, sources.json and model-contract.json: reproducibility, provenance and ORM handoff.
- FILES.json: packaged file allowlist; the repository's sibling ../d03-transactions-files.json drives integration packaging. No data directories, .lab-state.json, .venv, caches or credentials belong in the archive.

## Safe shutdown and recovery

```bash
uv run --locked python labctl.py stop
uv run --locked python labctl.py status
uv run --locked python labctl.py start
uv run --locked python labctl.py stop
```

Stop checks the marker, PID-directory relationship and healthy server identity before fast shutdown of its explicit -D, then waits. Status reports running=false and pg_ctl_status=3. Fast shutdown disconnects this cluster's clients, rolls back uncommitted work and retains committed data/logs. It never signals unrelated postgres processes, invokes brew services or deletes directories. Start after stop resumes storage, not initdb.

For connection failure inspect status and the printed root's server.log; for version mismatch inspect PG_BIN; for missing tables check preparation. Ownership/identity mismatch refuses reset and stop: investigate rather than deleting markers or substituting a user database. Partial first startup attempts to stop only its newly allocated directory and preserves the error. Inspect status/logs before proceeding; never reinitialize old storage. When a health/identity check itself is impossible, the controller refuses rather than guessing. Never use killall as a fallback.

At a break, record lab path, root, last command, tests, SQLSTATE and next action. After OS cleanup of /tmp, begin with a fresh extraction rather than treating unmarked old data as a new cluster.

## Limits and official sources

Normal stop/start is not disaster recovery. No production backup restore, power loss, ambiguous network commit, full Serializable matrix, real deadlock, authentication, authorization, pooling or load test is claimed. Later ORM work must preserve constraint names/types and failure tests. updated_at is not automatic. Owner existence and creator authorization are not fully enforced by foreign keys.

Official sources checked 2026-09-28. psycopg's docs site returned 403, so the official repository's fixed 3.3.6 documentation sources were read. PostgreSQL 18 docs and the 18.6 release page were accessible.

- https://www.postgresql.org/docs/18/tutorial-transactions.html
- https://www.postgresql.org/docs/18/transaction-iso.html
- https://www.postgresql.org/docs/18/explicit-locking.html
- https://www.postgresql.org/docs/18/ddl-constraints.html
- https://www.postgresql.org/docs/18/errcodes-appendix.html
- https://github.com/psycopg/psycopg/blob/3.3.6/docs/basic/transactions.rst
- https://www.postgresql.org/docs/release/18.6/
