# Product delivery templates

These files are a canonical, provider-neutral starting point for adapting the V4 product to a real target. They are templates, not a deployed application and not a substitute for the learner's own S03 authorization, database models, migrations, or O04-O06 operations evidence.

## Adaptation order

1. Copy the empty `starter/` directory into the learner's own product repository. Later, copy the reviewed operations files under `ops/` and `.github/workflows/`.
2. Replace the `app`, `migrations`, health route, image, domain, service account, database service names, and secret references.
3. Review the target Docker Engine, Linux/systemd, Caddy, PostgreSQL, CI, and secret store versions against official documentation.
4. Run the verification job against a disposable PostgreSQL service.
5. In an approved target, execute a reviewed migration, start the application, check real HTTPS, and run authenticated/unauthorized smoke cases.
6. Rehearse backup, isolated restore, application rollback, and session/membership invalidation before invited use.

No file contains credentials. `product.service.template` is the systemd alternative to the Compose path; use one process supervisor for a given target. `commands/release.sh` refuses to run without an immutable app/Caddy digest, a format-valid integration record with V0–V3 passing, passing build, migration, backup/restore, and rollback evidence, human approval, backup policy, and rollback owner. It still does not certify the backend or public operation. `commands/restore.sh` accepts only a fresh `restore_` database name and does not provide an overwrite or `--clean` fallback.

The `release` job deliberately fails until the learner implements and reviews `ops/deploy-approved.sh`. A green CI verification job is not a deployment approval. The backup and restore scripts require a reviewed `pg_service.conf` and protected passfiles; do not put passwords in service files, arguments, or repository variables.

## Files

- `starter/`: intentionally empty V0 product layout with no implementation or lockfile.
- `Dockerfile`, `.dockerignore`, `compose.production.yaml`: image, context, network, secrets, volumes, and process boundaries.
- `Caddyfile.template`: same-host/container reverse-proxy starting point.
- `product.service.template`: Linux/systemd alternative.
- `.github/workflows/verify-and-release.yml.template`: disposable CI database, locked verification, environment approval, and an explicit deploy adapter gate.
- `commands/release.sh`: target release skeleton.
- `commands/backup.sh`, `commands/restore.sh`, `pg_service.conf.template`: controlled backup and isolated restore skeleton.
- `app/secret_config.py`, `app/healthcheck.py`: application adapters that must be connected to the learner's actual app.
- `product-workbook.md`: stage-by-stage work package for turning the labs into your own product.


Official mechanisms used here: [uv Docker integration](https://docs.astral.sh/uv/guides/integration/docker/), [Docker build best practices](https://docs.docker.com/build/building/best-practices/), [Caddy automatic HTTPS](https://caddyserver.com/docs/automatic-https), [GitHub Actions environments](https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments), and [PostgreSQL pg_restore](https://www.postgresql.org/docs/18/app-pgrestore.html).
## Integration evidence record

`templates/integration-record.json` records V0 through V5 as learner declarations. Copy it to your product repository, replace the placeholder product identity, and update the stage/evidence statuses as work progresses.

Run the format checker from the unpacked archive:

```bash
python3 check_integration_record.py templates/integration-record.json
```

The checker validates field shape, stage/evidence consistency, relative artifact references, UTC timestamps, and obvious embedded credentials. It does not open referenced files, execute tests, inspect the backend, prove redaction, award graduation, or authorize public operation. A passing record is still subject to artifact and human review.
- `templates/product-contract.md`: V0 product contract template.
- `templates/integration-record.json`: V0–V5 evidence declaration checked for format only.
- `templates/incident-record.template`: incident and repair record.
- `templates/maintenance-record.template`: recurring maintenance evidence record.
- `check_integration_record.py`: format checker; it never executes the product or approves release.
