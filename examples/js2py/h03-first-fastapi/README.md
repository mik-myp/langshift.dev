# H03 — First synchronous FastAPI service

[简体中文](README.zh-cn.md) · [繁體中文](README.zh-tw.md)

This standalone local lab turns ordinary functions into a read-only task HTTP
service. It assumes H02's HTTP concepts and L13's decorators, not prior backend
framework experience. It imports no earlier chapter's implementation. The web
chapter explains mechanisms; this README keeps the runnable contract with the code.

## Environment and working directory

Verified on **2026-09-28**, macOS arm64: CPython **3.13.15**, uv **0.12.13**,
FastAPI **0.135.1**, Uvicorn **0.42.0**, Pydantic **2.12.5**. These are fixed tested
versions, not a claim to be latest. `uv.lock` pins transitive packages from public
PyPI, including Starlette 1.7.0 and pydantic-core 2.41.5. `requires-python` is
`>=3.13,<3.14`; `[tool.uv] package=false` runs local files without packaging them.
No frontend dependency, API key, database, pytest, or httpx is needed.

Enter the extracted `h03-first-fastapi` folder. In the repository, enter
`examples/js2py/h03-first-fastapi`. All commands below assume that directory.

```bash
uv --version
uv python install 3.13.15
uv sync --locked
uv run --locked python --version
```

For the maintainer's isolated reproduction environment, export before running uv:

```bash
export PATH="$HOME/.local/bin:$PATH"
export UV_PYTHON_INSTALL_DIR=/tmp/langshift-js2py-python-20260928
export UV_CACHE_DIR=/tmp/langshift-js2py-uv-cache-20260928
```

Those `/tmp` directories are disposable infrastructure, not project contents.
Ordinary learners can use uv's normal locations. Do not regenerate the lockfile
just to run the lab. Maintainer resolution used `uv lock --default-index https://pypi.org/simple`;
installation and execution use `--locked`.

## Start, request, stop

Terminal A:

```bash
uv run --locked python -m uvicorn app:app --host 127.0.0.1 --port 8003 --workers 1
```

`app:app` imports module `app` from this directory and retrieves its `app` object.
Import registers routes; Uvicorn opens the listener. `python app.py` only imports
and defines things, then exits. Explicit `--workers 1` avoids inherited worker
settings; it does not make synchronous handlers run serially. Do not use reload
for this first experiment. Never bind this unauthenticated lab to `0.0.0.0`.

Terminal B:

```bash
curl -sS -i http://127.0.0.1:8003/health
curl -sS -i http://127.0.0.1:8003/tasks/1
curl -sS -i 'http://127.0.0.1:8003/tasks?limit=1&offset=1'
bash requests.sh
```

`-sS` suppresses progress but shows connection failures; `-i` includes status and
headers. Quote `&` in query URLs. The worksheet sends **11** visible requests; it
prints evidence rather than asserting correctness. curl's default exit status is
not an assertion that the HTTP status was successful. API testing and fixtures
are formally taught in H06, not hidden requirements here.

Expected single-task result:

```http
HTTP/1.1 200 OK
content-type: application/json

{"id":1,"title":"Read HTTP","minutes":25,"done":false,"note":null}
```

Variable headers are omitted above. The second page contains only id=2, with
`limit=1`, `offset=1`, `total=2`. Stop **your own** foreground server with Ctrl-C
in terminal A. A subsequent client call fails to connect: it does not receive 404.

## Contract

- `GET /health`: 200, `{"status":"ok"}`. This is process liveness, not database readiness.
- `GET /tasks`: 200, `{items, limit, offset, total}` ordered by ascending id.
  Default limit 20 (1–100); default offset 0 (nonnegative). Beyond the end is an
  empty 200 page, not 404. `total` counts all records.
- `GET /tasks/{task_id}`: positive parsed integer; id 1/2 returns 200, absent id
  returns 404 with `{"detail":"Task not found"}`. Bad text or nonpositive id: 422.
- No writes. `POST /tasks` returns 405. Unknown route: 404, `Not Found`.
- Public fields are `id`, `title`, `minutes`, `done`, `note`. The two fixed records
  connect to H04's later contract but no Pydantic body model is taught here.
- `/docs` and `/openapi.json` expose the generated contract; opening them is not
  acceptance of route behavior.

## Deliberate failures and recovery

1. Keep your service running and repeat its startup command in another terminal.
   The second process exits nonzero with `address already in use`; the original
   still answers `/health`. Do not kill another user's listener. Stop the server
   you started or choose a different free port and update client URLs together.
2. Stop your server. From this folder's parent, run:

   ```bash
   uv run --project h03-first-fastapi --locked python -m uvicorn app:app --host 127.0.0.1 --port 8003 --workers 1
   ```

   Expect `Could not import module "app"`. Environment selection did not change
   the current directory. Recover by entering the lab folder, or add
   `--app-dir h03-first-fastapi` from the parent. `app:missing` instead reports
   `Attribute "missing" not found`: inspect the colon's two sides separately.
3. In the lab root, start the explicitly broken application:

   ```bash
   uv run --locked python -m uvicorn errors.broken_app:app --host 127.0.0.1 --port 8003 --workers 1
   ```

   From terminal B, request `curl -sS -i http://127.0.0.1:8003/broken`. Expect 500,
   body `Internal Server Error`, and a server traceback containing
   `RuntimeError: deliberate failure for H03`. Stop it, restart `app:app`, and
   recheck `/health` and `/tasks/1` for 200. Startup errors, input 422, missing 404,
   and application 500 belong to different layers.

## Independent work and restart notes

Rebuild the service in a new directory using only the environment files and this
contract. Explain import, registration, validation, handler execution, and JSON
serialization. Then add `/summary` for unfinished-task count/minutes; expect
`{"count":1,"minutes":25}`. Do not inspect the reference before attempting it.
The independent reference owns its own seed data and can be run with:

```bash
uv run --locked python -m uvicorn solutions.rebuild:app --host 127.0.0.1 --port 8003 --workers 1
```

Keep a recovery note with your working directory, app entry, last successful
command, request/status/body, current port and owning terminal, unresolved issue,
and next command. Record whether your server is stopped. These read-only seeds
are recreated on import; they are not saved user data.

## Files, packaging, and limits

- `app.py`: complete service; `requests.sh`: readable HTTP worksheet.
- `errors/broken_app.py`: intentional 500; `solutions/rebuild.py`: independent answer.
- `.python-version`, `pyproject.toml`, `uv.lock`: reproducible environment.
- `README*.md`, `SOURCES.md`, `VERIFICATION.md`: operation, sources, observed evidence.

The sibling **h03-first-fastapi-files.json is a positive allowlist** for displayed
and downloadable files. Only its entries may be packaged. Never recursively zip
the directory: exclude `.venv`, `__pycache__`, caches, `.env`/credentials, logs,
editor files, and personal data. `.gitignore` is defense in depth, not the archive
allowlist. Shared loaders/ZIP generation are integrated separately by the owner.

This is local, single-worker, sequential, read-only acceptance. It establishes no
concurrency, authentication, production deployment, browser CORS, proxy/TLS,
performance, or cross-platform guarantee. A Python syntax check is not API
acceptance. See **VERIFICATION.md** for actual request/startup cases and
**SOURCES.md** for official references checked on 2026-09-28.
