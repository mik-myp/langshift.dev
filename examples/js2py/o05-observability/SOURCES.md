# Official sources checked live — 2026-09-28

This laboratory is a local operations slice, not a claimed production deployment.
The actual versions are pinned in pyproject.toml and the public-PyPI uv.lock.

- [PostgreSQL18 backup overview](https://www.postgresql.org/docs/18/backup.html)
- [pg_dump: format, snapshot, scope and security](https://www.postgresql.org/docs/18/app-pgdump.html)
- [pg_restore: target, errors, single transaction, ownership](https://www.postgresql.org/docs/18/app-pgrestore.html)
- [SQL dump backup and restore](https://www.postgresql.org/docs/18/backup-dump.html)
- [pg_dumpall and cluster-global objects](https://www.postgresql.org/docs/18/app-pg-dumpall.html)
- [Roles and privileges](https://www.postgresql.org/docs/18/ddl-priv.html)
- [PostgreSQL logging configuration](https://www.postgresql.org/docs/18/runtime-config-logging.html)
- [Alembic official tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [GitHub Actions workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [Official checkout v4.2.2 commit reference](https://api.github.com/repos/actions/checkout/git/ref/tags/v4.2.2)
- [OWASP Logging Cheat Sheet official repository](https://github.com/OWASP/CheatSheetSeries/blob/master/cheatsheets/Logging_Cheat_Sheet.md)
- [Python3.13 logging](https://docs.python.org/3.13/library/logging.html)
- [Google SRE monitoring](https://sre.google/sre-book/monitoring-distributed-systems/)

OWASP's documentation page and the Psycopg documentation site returned 403 on
fetch; official repository source was used where available. Moving documentation
pages are cited for mechanisms, not a claim that the pinned versions are latest.
The checkout tag was resolved to commit 11bd71901bbe5b1630ceea73d27597364c9af683.
No hosted workflow was triggered or verified. Runtime PostgreSQL tools all report
18.6; cross-major or cross-platform recovery has not been tested.

D/S contracts checked: d04-d06-v1 and s01-s03-v1. O01-O03 contract checked:
o01-o03-v1. Opaque Bearer tokens, database digests, expiry, active/revoked flags and
auth_version are used, not JWT. The database migrations here are a complete
independent operational contract snapshot, not a replacement migration directory
for an already deployed S application. Account/membership recovery policies and
the metrics thresholds are explicit teaching decisions, not universal guarantees.

Environment/port boundary review, also checked live on 2026-09-28:

- [libpq environment variables](https://www.postgresql.org/docs/18/libpq-envars.html)
- [libpq password-file selection](https://www.postgresql.org/docs/18/libpq-pgpass.html)
- [uv environment settings](https://docs.astral.sh/uv/reference/environment/)
- [uv configuration discovery and disabling it](https://docs.astral.sh/uv/concepts/configuration-files/)
- [Uvicorn host/port/logging settings](https://www.uvicorn.org/settings/)
- [Pinned Uvicorn0.42.0 startup implementation](https://github.com/Kludex/uvicorn/blob/0.42.0/uvicorn/server.py)

Direct Python entry points reject inherited PG settings rather than mutating the
caller's environment. A private empty passfile prevents default credential-file
lookup. Real simultaneous port0 children validate the pinned startup banner;
this is not a claim that every future Uvicorn log format remains compatible.
