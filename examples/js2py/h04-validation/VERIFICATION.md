# Verification — h04-validation

Date: **2026-09-28**. Real environment and official references: SOURCES.md.

## What actually ran

- Public-PyPI `uv lock`, `uv sync --locked`, and installed-version checks passed.
- **84 actual HTTP assertions** against spawned Uvicorn processes, using the
  Python standard library (`urllib.request`) over TCP, not TestClient or mocks.
- **89 named observations total**, including those HTTP assertions plus process
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
| runtime model probe | `process/probe` | exit 0 |
| patch probe | `process/probe` | exit 0 |
| start app:app | `process/probe` | PASS |
| empty list | `GET /tasks` | 200 |
| create with spelling preserved | `POST /tasks` | 201 |
| create zero and defaults | `POST /tasks` | 201 |
| stable page with nested filtering | `GET /tasks?limit=1&offset=1` | 200 |
| read filtering | `GET /tasks/1` | 200 |
| patch done preserves other fields | `PATCH /tasks/1` | 200 |
| empty patch no-op | `PATCH /tasks/1` | 200 |
| explicit false and zero | `PATCH /tasks/1` | 200 |
| replace note | `PATCH /tasks/1` | 200 |
| clear note | `PATCH /tasks/1` | 200 |
| empty string note | `PATCH /tasks/1` | 200 |
| restore note | `PATCH /tasks/1` | 200 |
| patch title spelling | `PATCH /tasks/1` | 200 |
| patch valid placeholder value | `PATCH /tasks/1` | 200 |
| missing title | `POST /tasks` | 422 |
| missing minutes | `POST /tasks` | 422 |
| empty title | `POST /tasks` | 422 |
| blank title | `POST /tasks` | 422 |
| unicode blank title | `POST /tasks` | 422 |
| long title | `POST /tasks` | 422 |
| numeric title | `POST /tasks` | 422 |
| null title | `POST /tasks` | 422 |
| bool minutes | `POST /tasks` | 422 |
| text minutes | `POST /tasks` | 422 |
| float minutes | `POST /tasks` | 422 |
| negative minutes | `POST /tasks` | 422 |
| null minutes | `POST /tasks` | 422 |
| integer done | `POST /tasks` | 422 |
| text done | `POST /tasks` | 422 |
| null done | `POST /tasks` | 422 |
| numeric note | `POST /tasks` | 422 |
| long note | `POST /tasks` | 422 |
| client id | `POST /tasks` | 422 |
| client user id | `POST /tasks` | 422 |
| client internal field | `POST /tasks` | 422 |
| unknown field | `POST /tasks` | 422 |
| malformed JSON | `POST /tasks` | 422 |
| before invalid patches | `GET /tasks/1` | 200 |
| patch null title | `PATCH /tasks/1` | 422 |
| patch null minutes | `PATCH /tasks/1` | 422 |
| patch null done | `PATCH /tasks/1` | 422 |
| patch blank title | `PATCH /tasks/1` | 422 |
| patch bool minutes | `PATCH /tasks/1` | 422 |
| patch text minutes | `PATCH /tasks/1` | 422 |
| patch float minutes | `PATCH /tasks/1` | 422 |
| patch negative minutes | `PATCH /tasks/1` | 422 |
| patch text done | `PATCH /tasks/1` | 422 |
| patch invalid note | `PATCH /tasks/1` | 422 |
| patch client id | `PATCH /tasks/1` | 422 |
| patch client user id | `PATCH /tasks/1` | 422 |
| patch long title | `PATCH /tasks/1` | 422 |
| patch long note | `PATCH /tasks/1` | 422 |
| patch client internal field | `PATCH /tasks/1` | 422 |
| patch mixed valid invalid | `PATCH /tasks/1` | 422 |
| invalid writes change nothing | `GET /tasks/1` | 200 |
| invalid creates consume no id | `POST /tasks` | 201 |
| explicit create null note | `POST /tasks` | 201 |
| missing read | `GET /tasks/999` | 404 |
| bad id | `GET /tasks/nope` | 422 |
| zero id | `GET /tasks/0` | 422 |
| negative id | `GET /tasks/-1` | 422 |
| zero limit | `GET /tasks?limit=0` | 422 |
| large limit | `GET /tasks?limit=101` | 422 |
| bad limit | `GET /tasks?limit=nope` | 422 |
| negative offset | `GET /tasks?offset=-1` | 422 |
| bad offset | `GET /tasks?offset=nope` | 422 |
| empty later page | `GET /tasks?offset=99` | 200 |
| missing patch | `PATCH /tasks/999` | 404 |
| delete | `DELETE /tasks/1` | 204 |
| deleted read | `GET /tasks/1` | 404 |
| second delete | `DELETE /tasks/1` | 404 |
| remaining order | `GET /tasks` | 200 |
| OpenAPI body contract | `GET /openapi.json` | 200 |
| start app:app | `process/probe` | PASS |
| restart loses data | `GET /tasks` | 200 |
| restart loses old id | `GET /tasks/2` | 404 |
| restart reuses id | `POST /tasks` | 201 |
| start solutions.remaining_app:app | `process/probe` | PASS |
| report empty | `GET /reports/remaining` | 200 |
| report seed Zero | `POST /tasks` | 201 |
| report seed Short | `POST /tasks` | 201 |
| report seed Long | `POST /tasks` | 201 |
| report seed Finished | `POST /tasks` | 201 |
| report filter | `GET /reports/remaining?max_minutes=20` | 200 |
| report zero | `GET /reports/remaining?max_minutes=0` | 200 |
| report negative | `GET /reports/remaining?max_minutes=-1` | 422 |

## Observed bodies, mutation boundaries and loss on restart

- First POST -> 201:
  `{"id":1,"title":"  Read HTTP  ","minutes":25,"done":false,"note":"keep me"}`.
- POST minutes=true -> 422, `int_type`, loc `["body","minutes"]`; no new record.
- PATCH done=true kept the original title, minutes=25 and note="keep me".
- Empty PATCH kept every field; explicit false/0 were applied; note text replaced,
  null cleared, and an empty string remained a valid value.
- Explicit title="Untitled" was applied even though it equalled the patch placeholder.
- Invalid and mixed-valid/invalid patches left the prior record unchanged.
- Invalid creates consumed no id; 120-character title and 1000-character note
  succeeded while the next lengths failed.
- Create, read, patch, and nested list items had **exactly** the public five keys.
  The handler returned a storage dump containing internal_tag; the response model
  filtered it. Client id/user_id/internal_tag fields were rejected.
- DELETE -> 204, **0 body bytes**; later GET and repeated DELETE -> 404.
- Before restart the list held ids 2,3,4. After stopping and starting a new process,
  GET /tasks -> `{"items":[],"limit":20,"offset":0,"total":0}`, old id=2 -> 404,
  and the next created id was **1 again**. This proves loss, not durability.
- The report variation returned `{"count":2,"minutes":15}` at threshold 20,
  `{"count":1,"minutes":0}` at 0, and 422 at -1 after four explicit seed POSTs.

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
started the service on 127.0.0.1:8004.

- `bash requests.sh`: **25 real curl responses**, all with the
  expected status sequence below; source files and uv.lock remained byte-identical.
- Status sequence: `200, 201, 201, 200, 200, 200, 200, 200, 200, 422, 422, 422, 422, 422, 422, 422, 422, 422, 422, 404, 200, 204, 404, 404, 200`.
- This is a second run, separate from the 84 maintainer HTTP assertions above.
- All processes started for this run were stopped; no unrelated listener was killed.
- After the worksheet only id=2 remained. A real stop/restart yielded an empty
  200 list again. This clean-copy replay independently reproduced data loss.

Three locale chapter code/output fences and source references match exactly;
three locale README code/output fences also match. All six chapter MDX files
compiled and server-rendered in an isolated check with the future loader import
substituted **in memory only**. This confirms local content syntax/rendering,
not shared loader integration, Code Hike production build or HTTP behavior.
