# Official sources and reproducibility record

Checked **2026-09-28**. These are primary project documentation, tagged project
source, and publisher release metadata, retrieved over HTTPS with HTTP 200.
Live documentation may change. The shipped lockfile and observed requests, not
an assumption about "latest", define the verified behavior.

## Actual environment

- macOS arm64; CPython 3.13.15; uv 0.12.13.
- Direct pins: FastAPI 0.135.1, Uvicorn 0.42.0, Pydantic 2.12.5.
- Locked runtime also includes Starlette 1.7.0, AnyIO 4.15.1,
  pydantic-core 2.41.5, h11 0.16.0. See uv.lock for the complete set and hashes.
- Release metadata: FastAPI/Uvicorn require Python >=3.10; Pydantic requires
  >=3.9. Our project deliberately restricts to >=3.13,<3.14 and tests 3.13.15.
- `uv lock --default-index https://pypi.org/simple` really resolved the lock;
  `uv sync --locked` really installed it. All registry sources in the lock are
  `https://pypi.org/simple`, with distribution URLs under `files.pythonhosted.org`.
- Installed version checks and actual HTTP acceptance are separate from package
  metadata compatibility. Successful installation alone is not API acceptance.

## References and teaching claims

1. [fastapi-first-steps](https://fastapi.tiangolo.com/tutorial/first-steps/): Application object, decorators, generated docs.
2. [fastapi-async](https://fastapi.tiangolo.com/async/): Normal def route functions are dispatched to a thread pool; one worker does not imply serial handlers.
3. [asgi-intro](https://asgi.readthedocs.io/en/latest/introduction.html): Server/application interface responsibilities.
4. [uvicorn-settings-pinned](https://github.com/Kludex/uvicorn/blob/0.42.0/docs/settings.md): module:attribute import, app-dir, loopback/port binding, workers and reload.
5. [fastapi-query](https://fastapi.tiangolo.com/tutorial/query-params-str-validations/): Extraction, defaults and validation declarations for query parameters.
6. [fastapi-path](https://fastapi.tiangolo.com/tutorial/path-params-numeric-validations/): Path integer constraints and entry validation.
7. [fastapi-errors](https://fastapi.tiangolo.com/tutorial/handling-errors/): HTTPException versus unhandled application errors.
8. [uv-lock](https://docs.astral.sh/uv/concepts/projects/sync/): Locking/syncing and rejecting stale lockfiles with --locked.
9. [fastapi](https://pypi.org/pypi/fastapi/0.135.1/json): Published FastAPI 0.135.1 dependency/Python metadata.
10. [uvicorn](https://pypi.org/pypi/uvicorn/0.42.0/json): Published Uvicorn 0.42.0 dependency/Python metadata.
11. [pydantic](https://pypi.org/pypi/pydantic/2.12.5/json): Published Pydantic 2.12.5 dependency/Python metadata.

## Retrieval caveats and local policy

The old `www.uvicorn.org/settings/` endpoint failed TLS retrieval; the official
repository's **0.42.0-tagged settings documentation** was retrieved instead.
Pydantic's live BaseModel API endpoint returned 403; its official **v2.12.5 source**
was used to confirm copy/update behavior. Neither failure was treated as proof
that documentation or a release did not exist.

The task field limits, original-spelling policy, route/status choices, empty-PATCH
no-op, and process-local ids are **this course lab's explicit contract**, not
universal framework requirements. The full capstone later adds projects,
authentication, database constraints and durability; none are silently assumed.
No credentials, API keys, or personal records were accessed for verification.
