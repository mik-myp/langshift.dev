# h06-api-testing: complete local lab

Read the matching H05/H06 lesson first. This folder is independent: it does not
import H04 or the sibling lab. Canonical Python, HTML and test files are displayed
by the textbook loader and included through the sibling `-files.json` allowlist.

## Environment and first run

Tested 2026-09-28: CPython 3.13.15, uv 0.12.13, FastAPI 0.135.1,
Uvicorn 0.42.0, Pydantic 2.12.5, Starlette 0.52.1, pytest 8.4.2.
HTTPX 0.28.1 is a development dependency for TestClient and the real client.
Requires Python >=3.13,<3.14; this is an application, so uv package=false.
Use a terminal in this extracted directory. The lock resolves from public PyPI.
Do not replace `uv sync --locked` with an unreviewed upgrade.

```bash
uv sync --locked
uv run --locked python -m pytest -q
TASKS_APP_NAME="Learning tasks" uv run --locked python -m uvicorn task_api.main:create_app --factory --host 127.0.0.1 --port 8006
```

The server stays running. Use a second terminal **in this same directory**:

```bash
uv run --locked python live_client.py --port 8006
```

The live client requires an empty disposable server, creates test records and
removes them in finally. It checks real sockets, strict rejection, PATCH states,
pagination, output filtering and 204/404 cleanup. Stop the server with Ctrl-C.
A repeated client run works because data is removed; IDs need not restart at 1.
A process restart does reset the in-memory data and ID sequence.

The urllib client attempts each owned ID separately. A failed DELETE or readback
is recorded without skipping later IDs. It reports CLEANUP FAILED with unconfirmed
IDs; inspect only those records before replaying. Cleanup failure exits nonzero.
If the body also failed, its original traceback is preserved and cleanup diagnostics
are printed separately; neither error is silently turned into success. It does
not delete unrelated records or promise success when the service is unavailable.

## Responsibilities and configuration

`task_api/main.py` composes the app and owns one store per app. `config.py` reads
and validates environment strings. `models.py` is the input/output boundary;
`store.py` changes memory without HTTP; `routes.py` maps HTTP to those operations;
`dependencies.py` supplies the store/settings/page and owns a temporary trace
file per request. No async lifespan, database, login or permission code is hidden.

TASKS_APP_NAME is required nonblank public display text, **not a secret**.
TASKS_MAX_PAGE_SIZE defaults to 100 and accepts ASCII decimal integers from 20
to 100; the lower bound preserves the default page size of 20. The configuration
is read once per factory call, not per request. A `.env` file is not loaded.
To change running configuration, stop and restart with the changed environment.
Direct Settings objects are trusted internal test inputs, not a validation API.

```bash
env -u TASKS_APP_NAME uv run --locked python -m uvicorn task_api.main:create_app --factory --host 127.0.0.1 --port 8006
TASKS_APP_NAME="Learning tasks" TASKS_MAX_PAGE_SIZE=bad uv run --locked python -m uvicorn task_api.main:create_app --factory --host 127.0.0.1 --port 8006
```

These two commands are **expected startup failures**, not successful API tests.
The final diagnostic names TASKS_APP_NAME or TASKS_MAX_PAGE_SIZE without echoing
its raw value. Correct the variable and repeat the first successful start command.
If the address is in use, stop your own previous server or choose another port;
do not kill an unknown process. Import errors usually mean the wrong directory
or an incomplete `task_api` folder; changing CORS will not repair those errors.

## Contract and limits

POST /tasks -> 201; GET /tasks and GET/PATCH /tasks/{id} -> 200;
DELETE -> 204 with no body. A missing positive ID is 404; invalid input is 422.
The server allocates integer IDs. Titles are 1..120 characters, nonblank, and keep
their spelling/whitespace. Minutes are ordinary nonnegative JSON integers, not
booleans, strings or floats. Done is strict bool, default false. Note is nullable
text, <=1000 characters, default null. PATCH distinguishes omission, assignment
and null; only note permits null. Extra request fields are rejected; internal_tag
never leaves the output model. GET /tasks returns items/limit/offset/total sorted
by ID; offset counts records, not ID values. limit is 1..100 and obeys the cap.

TRACE acquire/use/release messages describe a real TemporaryFile handle, not a
persistent audit log or database transaction. Explicit function scope releases
before normal response send. A clean release does not roll back mutations.
No production concurrency, durability, isolation between users, deployment,
network security, authentication or authorization claim is made. All listeners
are 127.0.0.1 only; there is no real user data or credential in this lab.

For each note PATCH state (omission/value/null), assert status 200 and the complete
expected record in both the PATCH response and a subsequent GET. The independent
empty-PATCH exercise starts with done=true, nonzero minutes and a note, then
requires both complete responses to equal the original record. An unchanged-looking
PATCH response alone cannot prove storage stayed unchanged.

## H06 test layers and real browser check

The ordinary suite has 48 tests: 44 original in-process cases, 2 real-client cleanup
regressions and 2 acceptance-mutation regressions. The independent solution has 3. The first test
constructs TestClient directly; fixtures are taught afterwards. Tests use a new
app/store per case. The overrides fixture snapshots and restores the mapping in
finally; the exact original callable is the key. Replacements do not prove the
original dependency works. TestClient runs the real app but no Uvicorn socket.

```bash
uv run --locked python -m pytest -q tests/test_first_request.py
uv run --locked python -m pytest -q solutions/test_independent.py
uv run --locked python -m pytest -q experiments/test_fixture_failure.py
uv run --locked python live_httpx.py --port 8006
uv run --locked python -m http.server 5506 --bind 127.0.0.1 --directory browser
```

The experiment intentionally exits 1 with **1 failed, 1 passed**: a failed
assertion does not prevent the override fixture restoring that *same* app.
It is excluded from the normal suite by testpaths. Do not hide the failure with
xfail. This ordered probe is not an ordinary order-independent test pattern.
The HTTPX command requires the Uvicorn terminal to remain running. Stop it before
changing ports/configuration; the browser uses API port 8006 explicitly.

Open http://127.0.0.1:5506 and click Run browser check. Expect browser POST 201,
GET 200, strict input 422 and cleanup DELETE 204. The browser itself performs
preflight and enforces CORS, unlike TestClient/HTTPX. In another terminal, serve
the same browser folder on 5507, open that origin, and expect a fetch failure and
no newly created task. Check the browser Network panel: OPTIONS is rejected.
A Python client can still call the API without Origin; CORS is not authentication.
Do not use no-cors, wildcard origins or disable browser security to make it green.
Stop both static servers and Uvicorn with Ctrl-C.

## Bounded maintainer regressions

```bash
uv run --locked python -m pytest -q tests/test_live_client_cleanup.py
```

Expected: `2 passed`. Both tests launch an owned fault server on an OS-selected
loopback port and run the actual client. A first DELETE=503 must not skip the
second ID; only the first remains and the client exits nonzero. The second test
also fails the body and checks its original traceback survives. Servers stop in
finally; no user server is touched. This harness is not an independent-exercise
prerequisite and requires no async test code.

```bash
uv run --locked python -m pytest -q tests/test_patch_readback_regression.py
```

Expected: `2 passed`. Only disposable copies receive the stale-response mutant:
empty PATCH returns the old record but stores defaults. The base note-state child
run must fail at the later GET (`1 failed, 2 passed`); the independent empty-PATCH
child must likewise fail (`1 failed`). The outer tests pass only when the exact
readback assertion catches it, not for collection/import errors. No canonical
service file is changed. The outer cases are already included in the 48 total.

## Packaging, recovery and evidence

Only files in the sibling allowlist belong to the downloadable lab. Explicitly
excluded: .venv, __pycache__, .pytest_cache, .env/.env.*, logs, credentials, editor
state, temporary files and local caches. Do not build a ZIP by recursively adding
this directory. The lock is included; interpreter installs and cache directories
are not. README translations preserve commands and outputs.

When pausing, record current directory, versions, last command and actual result,
server PID/port and whether you stopped it, data state, remaining failure and the
next action. Restart from the locked sync and the ordinary suite, then replay the
specific failed request. Passing Python syntax is not HTTP acceptance.

See SOURCES.md for live-verified official sources and version/scope details.
The optional repository maintainer script `scripts/test-js2py-http-foundations.py`
checks clean allowlist copies, both suites, expected failures, real local servers,
resource send timing and process cleanup. It is not a reader prerequisite and
does not replace the real-browser check. Production/database/TLS/load behavior
is deliberately unverified.
