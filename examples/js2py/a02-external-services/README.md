# A02 — External service lifetimes

Verified 2026-09-28. This is an independent local lab following S03, not the full
capstone. No other chapter source is imported. Prerequisites: Python functions,
exceptions, context managers, tests and the existing synchronous API/SQL/auth
foundations. A02 additionally builds on A01, L14 and H05.

## Reproduce from a clean download

Extract and enter `a02-external-services`. In the repository, enter `examples/js2py/a02-external-services`.
Use CPython 3.13.15, uv 0.12.13, pytest 8.4.2. Install the specified uv first;
its installation is not performed by this lab. FastAPI 0.135.1, Uvicorn 0.42.0, Pydantic 2.12.5, HTTPX 0.28.1, AnyIO 4.12.1, Starlette 0.52.1.
The web baseline follows H03–H06; the lifecycle dependencies follow H05–H06.
The actual public-PyPI lock includes artifact hashes. `requires-python` accepts
3.13 only and `tool.uv.package=false` runs local source without packaging it.
Do not delete the lock or replace the baseline with an unreviewed upgrade.

```bash
# Run from the extracted a02-external-services directory.
set -eu
export PATH="$HOME/.local/bin:$PATH"
export UV_PYTHON_INSTALL_DIR=/tmp/langshift-js2py-python-20260928
export UV_CACHE_DIR=/tmp/langshift-js2py-uv-cache-20260928
uv --version
uv python install 3.13.15
uv sync --locked
uv run --locked python --version
uv run --locked python socket_lab.py
uv run --locked python -m pytest -q
uv run --locked python -m pytest -q solutions
```

These `/tmp` locations isolate the verified interpreter/download cache. They
contain no application data. Network is needed to install locked public packages,
but running the lab never calls a paid/third-party service or uploads user data.

## Stable demo transcript

The source of this transcript is `expected-socket-output.txt`; execution must match it.

```text
socket: normal hint available; upstream connection reused
socket: unavailable -> unavailable; core read ok
socket: malformed -> unavailable; core read ok
socket: wrongshape -> unavailable; core read ok
socket: oversized -> unavailable; core read ok
socket: slow -> unavailable; core read ok
socket: core create/update/read/delete finished while upstream held
socket: lifespan client closed
```

Main tests: **32 passed**. Independent reference tests: **4 passed**.
Elapsed time is intentionally not a correctness assertion. Python warnings are
errors except in the deliberately captured warning diagnostic. Main tests do not
silently include answer tests; run both commands.

## File map and real evidence

- `lifecycle.py`: loopback allowlist, shared client, phase timeouts, bounded cleanup shield.
- `app.py`: explicit lifespan, synthetic in-memory CRUD, separate optional hint endpoint.
- `service.py`: whole-operation budget, shared admission limit, two read-only GET attempts,
  bounded raw body, strict schema, redacted fallback, propagated cancellation.
- `faults.py`: test-only modes ok/unavailable/flaky/malformed/wrongshape/oversized/slow/hold.
- `socket_lab.py`: two real Uvicorn servers on automatically assigned 127.0.0.1 ports.
- `tests/test_service.py`: 27 policy/ASGI/diagnostic tests; fakes do not prove network timing.
- `tests/test_socket.py`: 5 real-TCP tests including peer EOF on normal/error/cancel exits,
  rejected use after client close, and usable shared capacity after cancelling one borrow.
- `solutions/receipts.py` and its tests: lost-reply/idempotency exercise and its restart limitation.

Manual servers (separate terminals, this same working directory):

```bash
uv run --locked uvicorn faults:create_fault_app --factory --host 127.0.0.1 --port 8766
uv run --locked uvicorn app:create_app --factory --host 127.0.0.1 --port 8765
```

The app's default upstream is port 8766. Use only synthetic task titles; `/control`
is test-only. Stop only your two terminals using Ctrl-C. For port conflicts use
`socket_lab.py`; never kill an unfamiliar process. The automatic harness stops only
its own Server objects and closes its own sockets.

## Failures, exercises and recovery

`uv run --locked python -m errors.config` must exit 1 with a redacted final message.
The fixture URL is fake; raw tracebacks can still contain source lines, so do not
expose them to users. `uv run --locked python -m errors.untrusted` must exit 1 with
ValidationError. Parseable JSON is not necessarily acceptable external data.

Guided change: allow one attempt and one concurrent operation; update policy-specific
counts, not the fake's behavior. Independent change: reproduce a lost reply with a
stable idempotency key; the same key/body must create one effect, conflicting bodies
must fail, cancellation must not retry, and restart must expose the fake's lack of durability.

Recovery card: current file, versions, last successful command, which 32+4 tests passed,
first failing scenario, next focused test. For missing app.state check lifespan; for
unexpected closed clients check whether a request closed the application's client.

## Safety and unproven boundaries

Only explicit `http://127.0.0.1:<port>` origins are accepted. There is no real credential,
user data, paid service, environment-secret reader or redirect-following. HTTPX proxy
inheritance is disabled. Core CRUD is in-memory, loses data on restart, and has no auth:
never expose it publicly or substitute it for the capstone's SQL/permission design.

Read-idle timeout is real-socket tested. Connect/write/pool failure policies include
mock tests, not complete network phase certification. TLS, real DNS, HTTP/2, multi-worker
capacity, forced process death and other AnyIO backends are untested. Tests explicitly
cancel owner Tasks; they do not claim every HTTP disconnect cancels a server handler.
BackgroundTasks and in-memory queues are not durable delivery systems.

## Download/source contract

`DOWNLOAD-ALLOWLIST.json` mirrors the repository's same-named-lab `-files.json` list.
Only those regular files may be archived. Environments, caches, credentials and real
business data are excluded. The site loader reads the same files shown in the chapter.
`sources.json` records official source URLs and the verification date. Package hashes
are supplied by public PyPI in uv.lock, not fabricated by a packaging script.
