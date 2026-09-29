# H04 — Pydantic input/output boundaries and in-memory CRUD

[简体中文](README.zh-cn.md) · [繁體中文](README.zh-tw.md)

A complete standalone local API, not a production store. Prerequisites are H03's
synchronous HTTP service and L11/L12 annotations/models. This lab imports no
implementation from another chapter. API test automation and fixtures are taught
in H06; the learner acceptance here uses fully visible curl requests.

## Reproduce the environment

Verified **2026-09-28**, macOS arm64: CPython **3.13.15**, uv **0.12.13**, FastAPI
**0.135.1**, Uvicorn **0.42.0**, Pydantic **2.12.5**. These are tested pins, not a
latest-version claim. Public-PyPI `uv.lock` also pins transitive packages, including
Starlette 1.7.0 and pydantic-core 2.41.5. `requires-python` is `>=3.13,<3.14`;
`[tool.uv] package=false`. No frontend dependency, database, API key, httpx, or
pytest is required.

Work in the extracted `h04-validation`, or `examples/js2py/h04-validation` in the
repository. All app/probe/solution commands below assume this directory.

```bash
uv --version
uv python install 3.13.15
uv sync --locked
uv run --locked python --version
```

Maintainer isolation, set before uv commands:

```bash
export PATH="$HOME/.local/bin:$PATH"
export UV_PYTHON_INSTALL_DIR=/tmp/langshift-js2py-python-20260928
export UV_CACHE_DIR=/tmp/langshift-js2py-uv-cache-20260928
```

Learners may use uv's normal locations. These temporary directories are not
project inputs. Normal runs never regenerate the lock. Maintainer resolution used
`uv lock --default-index https://pypi.org/simple`; use `--locked` for sync/run.

## The body and route contract

| Field | Create | PATCH |
| --- | --- | --- |
| title | Required str, 1–120 characters, not whitespace-only; preserve original spelling/spaces | Omitted preserves; valid string replaces; null rejected |
| minutes | Required strict nonnegative int; reject bool, text, float | Omitted preserves; 0 included; null rejected |
| done | Strict bool, default False | Omitted preserves; explicitly apply false too; null rejected |
| note | str or None, max 1000 characters, default None; empty string allowed | Omitted preserves; string replaces; null clears |
| id | Server generates a positive process-local integer | Client field rejected |
| internal_tag | Server adds `h04-memory-only` | Client field rejected; never public |

Lengths are Python string lengths, not bytes or visual graphemes. Unknown fields,
including `id`, `user_id`, and `internal_tag`, are rejected with 422. Rejecting a
claimed identity is not authenticating one: no user identity exists in this lab.

- `GET /health`: 200, `{"status":"ok"}`.
- `POST /tasks`: 201, full public task. Missing, malformed, or invalid body: 422.
- `GET /tasks`: 200, `{items, limit, offset, total}` ordered by id. `limit=20`
  defaults, range 1–100; `offset=0` defaults, nonnegative. Invalid query: 422.
  An offset beyond the end returns an empty page, not 404.
- `GET /tasks/{task_id}`: 200, public task; valid absent id: 404; invalid id: 422.
- `PATCH /tasks/{task_id}`: 200, full updated public task; `{}` is a no-op.
  Invalid fields: 422; valid body for missing record: 404.
- `DELETE /tasks/{task_id}`: 204, **zero body bytes**; missing/repeated delete: 404.

There is no PUT, authentication, user isolation, project relationship, idempotency
key, or final-capstone status enum. Public tasks contain exactly `id`, `title`,
`minutes`, `done`, `note` on create/read/patch and within list items.

## Understand the model flow before sending requests

`models.py` separates `TaskCreate`, `TaskPatch`, `TaskStored`, and `TaskPublic`.
Input uses strict types and rejects extra keys. The title validator checks
`value.strip()` but returns the original `value`. Public output intentionally
ignores fields outside its allowlist; `TaskPage` applies it to nested list items.

Run two small explanatory experiments:

```bash
uv run --locked python probe_models.py
uv run --locked python probe_patch.py
```

The first contrasts loose conversion of `"25"` with strict rejection of `True`,
`"25"`, `25.0`, and rejection of negative integers. It proves `str | None` without
a default is still required. These are model experiments, not HTTP acceptance.

`TaskPatch` has valid placeholders (`title="Untitled"`, `minutes=0`, inherited
`done=False`, `note=None`) so omitted nonnullable fields can be constructed.
**Only `model_dump(exclude_unset=True)` may be merged into storage.** Placeholders
are not update instructions. Explicit false, zero, a default-equal title, and null
must survive. `exclude_none` loses clearing intent; `exclude_defaults` loses false
and zero. The probe prints both correct merges and deliberately wrong dumps.

`app.py` builds a temporary merged dictionary and calls `TaskStored.model_validate`
before replacing the original record. `model_copy(update=...)` does not itself
validate updates. Server-generated id/internal data never comes from the request.
Handlers deliberately return full storage dictionaries; `response_model` filters
HTTP output. This avoids confusing “the internal key was never stored” with
“the public model actually filtered it.”

## Start an empty service and use the worksheet

Terminal A:

```bash
uv run --locked python -m uvicorn app:app --host 127.0.0.1 --port 8004 --workers 1
```

Do not enable reload or expose `0.0.0.0`. `--workers 1` explicitly overrides an
inherited worker default, but does not prevent thread-pool concurrency.
Terminal B:

```bash
curl -sS -i http://127.0.0.1:8004/tasks
bash requests.sh
```

`requests.sh` starts from empty memory and sends **25** visible requests. It
prints responses and does not assert success. Read them: curl's default exit code
can still be zero for an HTTP error. `-i` shows status/headers, `-X` selects method,
`-H 'Content-Type: application/json'` identifies JSON, and `--data-binary` sends
exact body text. Quote JSON and URLs containing `&`.

Check the sequence:

1. Empty list, two 201 creations, second page id=2/total=2. Preserve title spaces.
2. PATCH done preserves note; `{}` preserves everything; false and 0 are applied;
   note supports string replacement and explicit null clearing.
3. All eight invalid bodies return 422 without new records.
4. Bad path/query returns 422; valid missing id returns 404.
5. GET reflects storage; DELETE has zero body bytes; GET/repeated delete gives 404;
   the last list contains only id=2. No task response includes `internal_tag`.

The first created task's actual body is:

```json
{"id":1,"title":"  Read HTTP  ","minutes":25,"done":false,"note":"keep me"}
```

Sending `minutes=true` yields 422, with `loc=["body","minutes"]` and
`type="int_type"`. This differs from a valid-but-missing id's 404. Validation can
echo bad input, so use fictional data only and do not treat the default error
format as a production redaction policy.

Also manually cover missing title/minutes, `done=1`, `note=1`, null nonnullable
fields, spoofed id/internal fields, malformed JSON, and title/note boundaries:
120/1000 accepted, 121/1001 rejected. Prepare long bodies in a local file if useful
and send `--data-binary @payload.json`. GET after a rejected PATCH must show no
partial modification. Record both status and fields, not only “request worked.”

## Destructive restart and recovery — disposable data only

With id=2 still present after the worksheet, Ctrl-C **your own** server in terminal
A and restart with the same command. GET `/tasks` must return empty items/total=0;
GET `/tasks/2` must return 404; the next created id is 1 again. This is observed
data loss and id reuse. There is no backup or database to recover the old state.
Recover the learning checkpoint by restarting empty and replaying the worksheet.
Do not kill unrelated listeners. For a port collision, stop your own server or
choose a free port and update all requests. For import errors, check the working
directory and the two sides of `app:app` before reinstalling anything.

## Independent rebuild and variation

In a new directory, keep only environment files and the contract. Write models and
CRUD yourself, explain all four model roles, and pass the request acceptance before
looking at the reference. Record one bug's symptom, layer, cause, fix, and recheck.

Then add `/reports/remaining?max_minutes=20`: aggregate unfinished tasks whose
minutes are at most the threshold; default 60, allow 0, reject negatives. Return
only count/minutes, independent of pagination. Create Zero/0/false,
Short/15/false, Long/90/false, Finished/10/true. Expect `{"count":2,"minutes":15}`
for 20, `{"count":1,"minutes":0}` for 0, and 422 for -1.

After attempting it, run the reference (stop your current server first):

```bash
uv run --locked python -m uvicorn solutions.remaining_app:app --host 127.0.0.1 --port 8004 --workers 1
```

This explicitly reuses `app` and `tasks` from **this lab**, starts empty, and adds a
route. POST the four records and verify the report over HTTP. It imports no other
chapter. Save a pause note with directory, entry point, last successful request and
body, own port/terminal, stopped/running state, unresolved issue, and next command.
Always record that restarting destroys memory.

## Files, positive allowlist, and unverified boundaries

The sibling **h04-validation-files.json** lists exactly the source/document files
permitted for display/download. Never recursively archive `.venv`, `__pycache__`,
uv caches, `.env`/credentials, logs, editor files, or personal data. `.gitignore`
is not the packaging allowlist. Shared loader/ZIP integration belongs to the owner.
SOURCES.md contains official references; VERIFICATION.md records observed cases.

Synchronous handlers run in a thread pool. One worker is not a lock; read/modify/
write and id allocation are not a business transaction. Two PATCH requests can
lose updates, and multiple workers have separate dictionaries. No persistence,
authentication, authorization, idempotent retry, concurrent load, cross-process
consistency, capacity, browser CORS, proxy/TLS, production redaction, or deployment
guarantee is claimed. Earlier language helpers do not provide those guarantees.
Syntax checks and model probes do not substitute for real HTTP acceptance.
