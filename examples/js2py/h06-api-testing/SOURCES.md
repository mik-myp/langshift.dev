# Verified primary sources — 2026-09-28

This is a tested baseline, not a claim to use the newest releases. CPython 3.13.15,
uv 0.12.13, FastAPI 0.135.1, Uvicorn 0.42.0, Pydantic 2.12.5,
Starlette 0.52.1, AnyIO 4.12.1 (locked transitive dependency), pytest 8.4.2; H06 adds HTTPX 0.28.1.

- [FastAPI 0.135.1: larger applications and APIRouter](https://github.com/fastapi/fastapi/blob/0.135.1/docs/en/docs/tutorial/bigger-applications.md)
- [FastAPI 0.135.1: dependency injection](https://github.com/fastapi/fastapi/blob/0.135.1/docs/en/docs/tutorial/dependencies/index.md)
- [FastAPI 0.135.1: yield dependency scopes](https://github.com/fastapi/fastapi/blob/0.135.1/docs/en/docs/tutorial/dependencies/dependencies-with-yield.md)
- [FastAPI 0.135.1: historical lifecycle changes](https://github.com/fastapi/fastapi/blob/0.135.1/docs/en/docs/advanced/advanced-dependencies.md)
- [FastAPI 0.135.1: dependency overrides](https://github.com/fastapi/fastapi/blob/0.135.1/docs/en/docs/advanced/testing-dependencies.md)
- [FastAPI 0.135.1: CORS](https://github.com/fastapi/fastapi/blob/0.135.1/docs/en/docs/tutorial/cors.md)
- [Starlette 0.52.1: TestClient](https://github.com/Kludex/starlette/blob/0.52.1/docs/testclient.md)
- [pytest 8.4.2: fixtures and teardown](https://github.com/pytest-dev/pytest/blob/8.4.2/doc/en/how-to/fixtures.rst)
- [HTTPX 0.28.1: transports](https://github.com/encode/httpx/blob/0.28.1/docs/advanced/transports.md)
- [Uvicorn 0.42.0: factory, host and port](https://github.com/Kludex/uvicorn/blob/0.42.0/docs/settings.md)
- [Pydantic 2.12.5: strict mode](https://github.com/pydantic/pydantic/blob/v2.12.5/docs/concepts/strict_mode.md)
- [uv 0.12.13: locked sync](https://github.com/astral-sh/uv/blob/0.12.13/docs/concepts/projects/sync.md)
- [Python 3.13: temporary files](https://docs.python.org/3.13/library/tempfile.html)

Official tagged documentation was fetched live on the verification date. The
Pydantic documentation site returned 403 and the Uvicorn site had a TLS fetch
failure; their official tagged repository documents were used instead. Public
PyPI metadata and a real public-PyPI uv lock were also checked.

Compatibility finding: initially resolving the unbounded transitive Starlette
selected 1.7.0, which passed but warned that its HTTPX adapter is deprecated in
favor of httpx2. These labs deliberately pin Starlette 0.52.1, whose published
full-extra contract supports HTTPX >=0.27,<0.29. Do not suppress this warning and
pretend the same combination was tested. Revalidate if upgrading.

The maintainer-only ASGI probe observed release before response start/body for
function scope, and after normal response send for request scope. A handled
HTTPException unwinds both scopes before the exception response is sent. Merely
observing cleanup after TestClient.get returns cannot establish send timing.

AnyIO lock refinement: AnyIO 4.15.1 warned about Starlette 0.52.1 using
its deprecated BlockingPortal alias. The public-PyPI lock selects AnyIO 4.12.1;
`uv sync --locked` plus the full suite was rerun without filtering warnings.
