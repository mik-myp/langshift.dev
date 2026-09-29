# Official sources and version review

Review date: **2026-09-28**. `source-verification.json` contains official-document
fetch receipts (URLs, byte counts and SHA-256), fallback failures, and public PyPI
metadata for the exact pins. It is provenance, not a substitute for live tests.

SQLAlchemy 2.0.54 is the deliberately chosen 2.0 maintenance release; the current
feature series had 2.1.1. Alembic 1.20.0 and psycopg/binary 3.3.6 are tested with
CPython 3.13.15 and a live PostgreSQL 18.6 server (`server_version_num=180006`).
Psycopg's tagged documentation includes Python 3.13 and PostgreSQL 18 in its
supported range. The binary wheel packages client libraries, not a server.
Web pins match H03–H06: FastAPI 0.135.1, Uvicorn 0.42.0, Pydantic 2.12.5,
HTTPX 0.28.1; Starlette 0.52.1 and AnyIO 4.12.1 match H05/H06's verified lock.
The original newer-Web exploration is not the delivered baseline.

## Primary documentation

- [SQLAlchemy Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [SQLAlchemy Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [SQLAlchemy psycopg dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg)
- [SQLAlchemy 2.0 release history](https://docs.sqlalchemy.org/en/20/changelog/changelog_20.html)
- [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Alembic autogenerate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
- [Alembic data migration cookbook](https://alembic.sqlalchemy.org/en/latest/cookbook.html#data-migrations-general-techniques)
- [Alembic release history](https://alembic.sqlalchemy.org/en/latest/changelog.html)
- [psycopg 3.3.6 installation](https://github.com/psycopg/psycopg/blob/3.3.6/docs/basic/install.rst)
- [psycopg 3.3.6 transactions](https://github.com/psycopg/psycopg/blob/3.3.6/docs/basic/transactions.rst)
- [PostgreSQL 18 EXPLAIN](https://www.postgresql.org/docs/18/using-explain.html)
- [PostgreSQL 18 constraints](https://www.postgresql.org/docs/18/ddl-constraints.html)
- [PostgreSQL 18 initdb](https://www.postgresql.org/docs/18/app-initdb.html)
- [PostgreSQL 18 pg_ctl](https://www.postgresql.org/docs/18/app-pg-ctl.html)
- [PostgreSQL 18.6 release notes](https://www.postgresql.org/docs/18/release-18-6.html)
- [pytest 8.4.2 safe fixtures](https://github.com/pytest-dev/pytest/blob/8.4.2/doc/en/how-to/fixtures.rst)
- [uv installation](https://docs.astral.sh/uv/getting-started/installation/)
- [PostgreSQL binary downloads](https://www.postgresql.org/download/)

The psycopg/pytest websites returned HTTP 403 during this review; the corresponding
official tagged documentation was fetched instead. No third-party tutorial is
used to infer compatibility. Alembic 1.20 supports optional, default-off named
CHECK detection; this lab does not enable it or imply it detects changed
expressions. EXPLAIN costs are relative planner units, not a stable benchmark.
