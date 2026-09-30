# Learner product starter

This is an intentionally empty V0 starter for the js2py integrated product. It has no business implementation, no reference answer, no lockfile, and no passing test claim.

## Start

```bash
uv python install 3.13.15
uv lock
uv sync --locked
```

At this point `pytest` will find no tests. That is not acceptance. Continue by writing your product contract and your first business rules.

## Required learner-created files

Create these files yourself:

- `docs/product-contract.md`
- `docs/integration-record.json`
- `src/product/` modules
- `tests/` business and failure tests
- later: API entry point
- later: `migrations/` and database tests
- later: `ops/` release and recovery runbooks

From the delivery archive, copy `templates/product-contract.md` to `docs/product-contract.md` and fill it in. Copy `templates/integration-record.json` to `docs/integration-record.json`. Commit both; they are product documentation, not generated cache.

The generated `uv.lock` is yours. Do not copy the chapter labs' locks or installed environments. Update it deliberately whenever you change dependencies.

## Boundary

This starter only fixes the initial responsibility layout. It does not implement tasks, API, PostgreSQL, authorization, async, deployment, or recovery. Those are the learner's V0—V5 work.
