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

1. [fastapi-body](https://fastapi.tiangolo.com/tutorial/body/): Binding a Pydantic model to a JSON request body.
2. [pydantic-strict](https://docs.pydantic.dev/latest/concepts/strict_mode/): Strict policy and differences between input forms; strict int rejection.
3. [pydantic-fields](https://docs.pydantic.dev/latest/concepts/fields/): Required versus nullable versus default; validating defaults.
4. [pydantic-validators](https://docs.pydantic.dev/latest/concepts/validators/): After field validators, classmethod, returning a value or raising ValueError.
5. [pydantic-serialization](https://docs.pydantic.dev/latest/concepts/serialization/): Explicitly supplied fields, exclude_unset, exclude_none and exclude_defaults.
6. [pydantic-copy-pinned](https://github.com/pydantic/pydantic/blob/v2.12.5/pydantic/main.py): BaseModel model_copy(update=...) does not validate update data; inspect the pinned implementation/docstring.
7. [pydantic-config](https://docs.pydantic.dev/latest/api/config/): strict, extra=forbid/ignore, validate_default.
8. [fastapi-response](https://fastapi.tiangolo.com/tutorial/response-model/): Public response model validation and nested output filtering.
9. [fastapi-update](https://fastapi.tiangolo.com/tutorial/body-updates/): Partial-update intent and exclude_unset; this lab explicitly revalidates its complete merged candidate.
10. [fastapi-async](https://fastapi.tiangolo.com/async/): Normal def route functions are dispatched to a thread pool; one worker does not imply serial handlers.
11. [uvicorn-settings-pinned](https://github.com/Kludex/uvicorn/blob/0.42.0/docs/settings.md): module:attribute import, app-dir, loopback/port binding, workers and reload.
12. [uv-lock](https://docs.astral.sh/uv/concepts/projects/sync/): Locking/syncing and rejecting stale lockfiles with --locked.
13. [fastapi](https://pypi.org/pypi/fastapi/0.135.1/json): Published FastAPI 0.135.1 dependency/Python metadata.
14. [uvicorn](https://pypi.org/pypi/uvicorn/0.42.0/json): Published Uvicorn 0.42.0 dependency/Python metadata.
15. [pydantic](https://pypi.org/pypi/pydantic/2.12.5/json): Published Pydantic 2.12.5 dependency/Python metadata.

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
