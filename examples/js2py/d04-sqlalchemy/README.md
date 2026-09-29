# D04: synchronous ORM and transaction ownership

Run locally, not in Pyodide. This directory is the complete canonical lab; it does
not import sibling labs. Download and webpage source are generated from the
explicit sibling `d04-sqlalchemy-files.json` allowlist.

## 1. Before the first command

Open a terminal in this extracted `d04-sqlalchemy` directory. CPython executes Python;
uv installs the locked Python packages into `.venv`. Neither installs/runs the
PostgreSQL server. PostgreSQL's `postgres`, `initdb`, `pg_ctl`, and `psql` binaries
must all be version 18 and from the same installation. `psycopg[binary]` bundles
client libraries, not a database server.

Verified on macOS arm64: Python 3.13.15, uv 0.12.13, PostgreSQL 18.6 at
`/opt/homebrew/bin`. If missing, first install uv and PostgreSQL 18 using their
official installers (see SOURCES.md); do not initialize an existing database or
start a system service. On another POSIX installation set `PG_BIN` to the
absolute directory containing those four executables. The `/opt/homebrew/bin`
line below is the verified machine's path, not a universal Linux path.
Do not run as root. This harness uses Unix sockets and is not verified on Windows.
No Docker, `brew services`, cloud account, password or secret is needed.

## 2. Install and execute

The temporary uv directories keep the shared-machine caches separate; they are
not database storage. `uv sync --locked` must fail rather than silently change
the lock. The lock was generated against public PyPI. Python is constrained to
`>=3.13,<3.14`, with `[tool.uv] package=false`.

```bash
export PATH="$HOME/.local/bin:$PATH"
export UV_PYTHON_INSTALL_DIR=/tmp/langshift-js2py-python-20260928
export UV_CACHE_DIR=/tmp/langshift-js2py-uv-cache-20260928
export PG_BIN=/opt/homebrew/bin
uv --version
"$PG_BIN/postgres" --version
uv python install 3.13.15
uv sync --locked
uv run --locked python pg_sandbox.py --evidence /tmp/d04-sqlalchemy-cleanup.json -- python -m pytest -q
uv run --locked python pg_sandbox.py -- python demo.py
uv run --locked python pg_sandbox.py -- python commit_failure.py
```

The tests should report **10 passed**. Runtime duration and paths vary.
SQLAlchemy 2.0.54 is a deliberate 2.0 maintenance-line pin, not a claim that 2.0
is the current feature series (2.1.1 was available on 2026-09-28). Alembic 1.20.0,
psycopg/psycopg-binary 3.3.6, FastAPI 0.135.1, Uvicorn 0.42.0, Pydantic 2.12.5, HTTPX 0.28.1 and
pytest 8.4.2 are pinned; transitive versions are in `uv.lock`.
The Web versions match H03–H06; ORM lessons do not introduce an unrelated framework upgrade. Starlette 0.52.1 and AnyIO 4.12.1 also match the verified H05/H06 lock.

## 3. What starts, what closes, what is protected

`pg_sandbox.py` uses `mkdtemp` for an owned cluster in `/tmp/ls-pg-*`. A cluster
is one PostgreSQL server's data directory, containing several databases; a test
database is one isolated namespace inside it. The server listens only on a
private Unix socket (directory/socket permissions 0700), not TCP. Local trust
authentication is acceptable only for this disposable, same-user lab: it is not
a production security recipe. The marker/token prevents accidental wrong-target
access; it is not a defense against hostile processes running as your OS user.

The harness runs `initdb`, starts only its own `pg_ctl -D <owned path>`, makes a
non-superuser `lab_owner` role with CREATEDB for fixtures, and creates a random
`js2py_lab_*` database. It strips inherited PG settings and database URLs.
Only the child command receives `LAB_DATABASE_URL` and the ownership marker.
`safety.py` refuses an ordinary dev/prod URL even if you rename an environment
variable. Tests each create a separate database, dispose their pools, then drop
only that database. DROP does not use FORCE: a leak must remain observable.

In `finally`, the runner stops its owned server with fast shutdown, checks
`pg_ctl status` (3 = not running), and removes only its owned directory. The JSON
proof has `server_version=180006`, `stopped=true`, `removed=true`, and
`status_after_stop=3`. A child exit failure still goes through cleanup. On stop
failure the directory/log is retained and the command fails; follow the printed
owned path, never kill every postgres process. SIGKILL or power loss cannot run
Python finally: inspect that exact owned directory/process before manual cleanup.

Every new sandbox invocation starts fresh. To keep a database across several
commands, use `uv run --locked python pg_sandbox.py -- bash`, execute commands
inside that shell, then `exit`. Nothing is exported permanently to your normal
shell. This intentional ephemerality is not a production persistence strategy.

## 4. Diagnosis rather than blind retry

| Observation | Diagnose / recover |
| --- | --- |
| PostgreSQL binary missing / wrong major | Check all four versions; correct PG_BIN, not a URL to your existing server. |
| `Refusing database access` | Use the wrapper; do not weaken the guard or point at development data. |
| `relation does not exist` | D04: run bootstrap inside this same sandbox. D05/D06: upgrade this database, not a previous disposable one. |
| `PendingRollbackError` / failed Session | End the failed unit of work, rollback or discard the Session; do not retry only the final INSERT. |
| Pool timeout / database still accessed | Close every Session/Connection; dispose after borrowers finish. Bigger pools hide leaks. |
| Migration rejects old data | Inspect revision and offending rows, fix by explicit policy, rerun; do not stamp past the failure. |
| Cleanup says stopped=false | Keep evidence/server.log; stop only its printed owned cluster before removing anything. |

## 5. Model continuity and boundaries

The four tables and original constraint names match D01–D03. H `done=false/true`
becomes `status=todo/done`; `doing` is new. H `note` becomes nullable `description`;
`minutes` remains an estimate; generated bigint identities replace in-memory IDs,
without automatically importing them. Project/User/ProjectMember and task FKs
are added explicitly. `updated_at` is not an auto-update trigger. SQL `btrim`
removes ordinary spaces, not all Python Unicode whitespace. All FKs use RESTRICT.
D05 adds `priority` via nullable expansion, backfill, default/NOT NULL/CHECK.
D06 preserves that head; its composite index is an experiment, not a hidden
schema change for downstream applications.

This is not authenticated multi-user software. Later S chapters must migrate
password hashes, active state and auth_version, derive creators from verified
identity, and enforce membership/ownership. FK validity alone is not permission.
Tests do not establish production performance, zero-downtime migrations,
network-partition recovery, backups, or authorization. Read the chapter's
exercise requirements before opening `solutions/`.

## 6. Pause / resume record

Save your code diff, current lab/revision, last successful command, passed tests,
remaining question, and the first next action. A temporary cluster will not
survive wrapper exit: save the data-generation commands, never copy database
files into the lab. Exclude `.venv`, `.pytest_cache`, `__pycache__`, `.env`, cluster
data, logs and real secrets from downloads. Only allowlisted source enters ZIPs.

Official source review and execution baseline: **2026-09-28**; see SOURCES.md.
