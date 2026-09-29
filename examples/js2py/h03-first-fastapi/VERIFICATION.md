# Verification — h03-first-fastapi

Date: **2026-09-28**. Real environment and official references: SOURCES.md.

## What actually ran

- Public-PyPI `uv lock`, `uv sync --locked`, and installed-version checks passed.
- **23 actual HTTP assertions** against spawned Uvicorn processes, using the
  Python standard library (`urllib.request`) over TCP, not TestClient or mocks.
- **35 named observations total**, including those HTTP assertions plus process
  startup/exit, expected command failures, and model probes where applicable.
  These totals do not count the reader worksheet or syntax/render checks.
- Each service bound only to **127.0.0.1**, with **--workers 1** and no reload.
  Ephemeral ports were allocated for isolation and recorded in maintainer evidence.
- Only child process groups started by the verifier were signalled at cleanup.
  SIGINT shutdown can give parent exit 0 or 130; neither is an HTTP status.
- Actual startup commands: `uv run --locked python -m uvicorn app:app --host
  127.0.0.1 --port <allocated-port> --workers 1`, or the documented failure/answer
  entry point. This source code contains no async handlers, lifespan setup, DI,
  database, authentication, hidden fixture or HTTP client dependency.

## Case ledger

`PASS` rows are process/probe observations, **not extra HTTP requests**. A 422/404/500
is success only where that exact failure was the intended acceptance result.

| Case | Request / action | Observed |
| --- | --- | --- |
| start app:app | `process/probe` | PASS |
| health | `GET /health` | 200 |
| read seed | `GET /tasks/1` | 200 |
| list | `GET /tasks` | 200 |
| page | `GET /tasks?limit=1&offset=1` | 200 |
| empty page | `GET /tasks?offset=99` | 200 |
| missing id | `GET /tasks/999` | 404 |
| text id | `GET /tasks/nope` | 422 |
| zero id | `GET /tasks/0` | 422 |
| negative id | `GET /tasks/-1` | 422 |
| zero limit | `GET /tasks?limit=0` | 422 |
| large limit | `GET /tasks?limit=101` | 422 |
| text limit | `GET /tasks?limit=nope` | 422 |
| negative offset | `GET /tasks?offset=-1` | 422 |
| unknown route | `GET /missing` | 404 |
| wrong method | `POST /tasks` | 405 |
| OpenAPI | `GET /openapi.json` | 200 |
| port collision | `process/probe` | exit 1 |
| original survives collision | `GET /health` | 200 |
| wrong working directory | `process/probe` | exit 1 |
| missing attribute | `process/probe` | exit 1 |
| import diagnostic | `process/probe` | exit 0 |
| python file is not server | `process/probe` | exit 0 |
| connection refused after stop | `process/probe` | exit 0 |
| start errors.broken_app:app | `process/probe` | PASS |
| unhandled application bug | `GET /broken` | 500 |
| traceback stays in log | `process/probe` | PASS |
| start app:app | `process/probe` | PASS |
| normal health recovery after 500 | `GET /health` | 200 |
| normal task recovery after 500 | `GET /tasks/1` | 200 |
| start app:app | `process/probe` | PASS |
| app-dir recovery from parent | `GET /health` | 200 |
| start solutions.rebuild:app | `process/probe` | PASS |
| independent summary | `GET /summary` | 200 |
| independent rebuild page | `GET /tasks?limit=1&offset=1` | 200 |

## Observed bodies and failure recovery

- `/tasks/1` -> 200:
  `{"id":1,"title":"Read HTTP","minutes":25,"done":false,"note":null}`.
- `/tasks?limit=1&offset=1` -> 200, id=2 only, total=2.
- `/tasks/999` -> 404, `{"detail":"Task not found"}`.
- `/tasks/nope` -> 422, type `int_parsing`, loc `["path","task_id"]`.
- Second server on the same port -> exit 1, `address already in use`; original
  `/health` remained 200. The macOS run reported Errno 48.
- Wrong directory -> exit 1, `Could not import module "app"`; explicit app-dir
  from the parent restored a 200 response. `app:missing` -> attribute error.
- `python app.py` -> exit 0 without a listener; importing the object printed FastAPI.
- Intentional `/broken` -> 500, body `Internal Server Error`; server log included
  `RuntimeError: deliberate failure for H03`. Restarting normal app restored 200.
- Stopping the normal listener produced connection refusal, not a fabricated 404.
- Independent `/summary` -> 200, `{"count":1,"minutes":25}`.

## Learner reproduction and limits

Start a fresh service with the README command and run `bash requests.sh` in
another terminal. Read each status/body and follow the restart/failure instructions;
the shell worksheet prints evidence but does not assert it. H06 will teach formal
API tests and fixtures. Keep a failure/recovery note, not only a green command.

The maintainer's full request/body/command evidence and rerunnable verification
script are kept under `/tmp/langshift-h03-h04-work/`, referenced from the integration
handoff. They are not hidden learning prerequisites or runtime dependencies.

Not established: concurrency correctness, persistence, authorization, browser CORS,
proxies/TLS, production redaction, capacity/load, cross-platform deployment, or
idempotent writes. No credential or real user data was used. Model probes, syntax
compilation, MDX rendering, and lockfile parsing are separate checks and are never
counted as HTTP acceptance. Shared site loaders, ZIP publication and full-site build
are intentionally left to integration; no claim of their completion is made here.

## Clean allowlist reproduction and reader worksheet

A separate directory was populated **only** from the positive allowlist (no
original `.venv`, cache, parent chapter or repository imports). There, `uv sync
--locked` created a new environment and the documented `--workers 1` command
started the service on 127.0.0.1:8003.

- `bash requests.sh`: **11 real curl responses**, all with the
  expected status sequence below; source files and uv.lock remained byte-identical.
- Status sequence: `200, 200, 200, 200, 404, 422, 422, 422, 422, 404, 405`.
- This is a second run, separate from the 23 maintainer HTTP assertions above.
- All processes started for this run were stopped; no unrelated listener was killed.

Three locale chapter code/output fences and source references match exactly;
three locale README code/output fences also match. All six chapter MDX files
compiled and server-rendered in an isolated check with the future loader import
substituted **in memory only**. This confirms local content syntax/rendering,
not shared loader integration, Code Hike production build or HTTP behavior.
