# Primary sources, version pins and local policy

核验 / Verified **2026-09-28**. This record applies to this independent lab.
Links below are primary project documentation, tagged project source or publisher
release metadata, retrieved over certificate-validated HTTPS. Live pages can
change. The shipped lock and executed PostgreSQL/HTTP cases define what was
actually verified; these pins are not advertised as the latest releases.

## Environment and resolution

- macOS arm64; CPython3.13.15; uv0.12.13; PostgreSQL18.6.
- Direct runtime pins: FastAPI0.135.1, Uvicorn0.42.0, Pydantic2.12.5,
  SQLAlchemy2.0.54, Alembic1.20.0, psycopg[binary]3.3.6, argon2-cffi25.1.0.
- Dev pin pytest8.4.2. `requires-python = ">=3.13,<3.14"`; `[tool.uv] package=false`.
- Real `uv lock --default-index https://pypi.org/simple` resolution and
  `uv sync --locked` installation. All registry entries are public PyPI,
  distribution URLs are files.pythonhosted.org and include real hashes.
- Locked runtime includes Starlette1.7.0, AnyIO4.15.1, pydantic-core2.41.5,
  argon2-cffi-bindings26.1.0 and h11 0.16.0. See uv.lock for the complete set.
- Release Python requirements are necessary compatibility checks, not proof of
  behavior. Real API/PG verification is recorded separately in VERIFICATION.md.

## Sources and precise claims

- [argon2-api](https://argon2-cffi.readthedocs.io/en/stable/api.html): Argon2id, per-hash random salt, verify exceptions and check_needs_rehash after successful verification.
- [argon2-parameters](https://argon2-cffi.readthedocs.io/en/stable/parameters.html): Explicit m=65536 KiB/t=3/p=4 profile; cost is not a capacity promise and must be measured on the target.
- [python-secrets](https://docs.python.org/3.13/library/secrets.html): 32 explicit random bytes for token_urlsafe; random bearer, not user-selected password.
- [python-hashlib](https://docs.python.org/3.13/library/hashlib.html): SHA-256 for high-entropy token lookup and validated-payload comparison, not password hashing.
- [python-datetime](https://docs.python.org/3.13/library/datetime.html): Aware datetime and UTC normalization; timezone representation cannot repair clock skew.
- [python-decimal](https://docs.python.org/3.13/library/decimal.html): String-to-Decimal construction and local precision context; no float-derived exact-money claim.
- [python-uuid](https://docs.python.org/3.13/library/uuid.html): UUIDv4 operation identifiers; canonical syntax is a lab contract, not authorization.
- [owasp-passwords](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html): Use mature adaptive password hashing; production account-security gates remain separate.
- [owasp-sessions](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html): Session lifecycle, expiry, regeneration/revocation and protected transport.
- [owasp-authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html): Deny by default, verify every request, and test object-level access with known IDs.
- [owasp-logging](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html): Exclude passwords, access tokens, session identifiers and sensitive connection details from logs.
- [postgres-isolation](https://www.postgresql.org/docs/18/transaction-iso.html): READ COMMITTED statement snapshots, including a losing ON CONFLICT insertion whose winner requires a later SELECT.
- [postgres-locking](https://www.postgresql.org/docs/18/explicit-locking.html): Shared/exclusive row locks, ordering, blocking and deadlock boundaries.
- [postgres-insert](https://www.postgresql.org/docs/18/sql-insert.html): ON CONFLICT DO NOTHING with an explicit unique target and RETURNING claim result.
- [postgres-constraints](https://www.postgresql.org/docs/18/ddl-constraints.html): Composite PK/FK/CHECK enforce data invariants, not caller authorization.
- [postgres-partial-indexes](https://www.postgresql.org/docs/18/indexes-partial.html): A unique owner-only index proves at most one owner, not at least one.
- [sqlalchemy-transactions](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html): The outer Session.begin owns commit/rollback; flush does not commit.
- [sqlalchemy-pg-insert](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#insert-on-conflict-upsert): PostgreSQL dialect insert.on_conflict_do_nothing target and returning.
- [fastapi-errors](https://fastapi.tiangolo.com/tutorial/handling-errors/): Adapt request-validation and expected DB errors without echoing sensitive input.
- [pydantic-secrets](https://docs.pydantic.dev/latest/api/types/#pydantic.types.SecretStr): SecretStr masks common representations; get_secret_value unwraps intentionally, not transport encryption.
- [alembic-tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html): Explicit revision history; no blind stamp or automatic destructive credential downgrade.
- [argon2-cffi](https://pypi.org/pypi/argon2-cffi/25.1.0/json): Publisher release 25.1.0; requires_python >=3.8.
- [SQLAlchemy](https://pypi.org/pypi/SQLAlchemy/2.0.54/json): Publisher release 2.0.54; requires_python >=3.7.
- [alembic](https://pypi.org/pypi/alembic/1.20.0/json): Publisher release 1.20.0; requires_python >=3.10.
- [psycopg](https://pypi.org/pypi/psycopg/3.3.6/json): Publisher release 3.3.6; requires_python >=3.10.
- [pytest](https://pypi.org/pypi/pytest/8.4.2/json): Publisher release 8.4.2; requires_python >=3.9.
- [fastapi-release](https://pypi.org/pypi/fastapi/0.135.1/json): Publisher release 0.135.1; requires_python >=3.10.
- [uvicorn-release](https://pypi.org/pypi/uvicorn/0.42.0/json): Publisher release 0.42.0; requires_python >=3.10.
- [pydantic-release](https://pypi.org/pypi/pydantic/2.12.5/json): Publisher release 2.12.5; requires_python >=3.9.
- [uv-release](https://pypi.org/pypi/uv/0.12.13/json): Publisher release 0.12.13; requires_python >=3.8.
- [python-release](https://www.python.org/downloads/release/python-31315/): Exact CPython 3.13.15 publisher release page; actual interpreter also checked locally.
- [postgres-release](https://www.postgresql.org/docs/18/release-18-6.html): Exact PostgreSQL18.6 release notes; actual SHOW server_version_num=180006 in every owned test cluster.
- [uv-package-tagged](https://raw.githubusercontent.com/astral-sh/uv/0.12.13/docs/concepts/projects/config.md): Tagged project configuration: package=false; environment used without packaging the lab.
- [uvicorn-settings-tagged](https://raw.githubusercontent.com/Kludex/uvicorn/0.42.0/docs/settings.md): Tagged process/binding options; serve.py fixes loopback and disables access logs.

- [Python urllib.request](https://docs.python.org/3.13/library/urllib.request.html): default environment proxy discovery, explicit `ProxyHandler({})` to disable it, and a no-redirect handler. A localhost URL alone does not protect credential routing.
- [PostgreSQL libpq environment](https://www.postgresql.org/docs/18/libpq-envars.html): implicit connection defaults including PGHOSTADDR/PGSERVICE; the lab clears PG* before opening connections and for owned database subprocesses.

## Retrieval failures and scope

The first Python Decimal and OWASP Authorization requests failed transient TLS
retrieval; retries succeeded with HTTP200. The uv settings endpoint returned403
and the legacy www.uvicorn.org settings endpoint failed TLS retrieval; official
tagged repository documentation was used instead. No certificate verification
was disabled, and a retrieval failure was not treated as proof that a release or
feature does not exist. The maintainer handoff retains retrieval statuses.

The account schema, 15–128-character provisioning rule, opaque-token design,
900-second default session lifetime, 404-versus403 policy, lock ordering, canonical
UUIDv4 key, 86400-second receipt lifetime and retained-expired-key409 behavior
are **explicit course contracts**, not universal framework defaults. The capstone's
JWT suggestion is deliberately replaced by opaque DB-backed sessions in this
track. There is no refresh token, public registration or invented cryptography.
D migrations001–003 are preserved; no H done/note alias is smuggled into the D
project schema. No external side effects or production safety are inferred from
passing local tests. No API key or personal credential was accessed.
