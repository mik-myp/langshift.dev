# js2py Product Workbook: turn chapter labs into your own service

This is not an implementation answer or a weekly schedule. Work by capability. Pause and resume when needed, consult official documentation, and keep reviewable evidence in your own product repository.

First copy `templates/integration-record.json` into your repository. Update evidence status as work progresses, and update `next_action` and the product revision when pausing. The format checker validates shape only; it never runs the product.

## V0: Your Python product foundation

Entry condition: L10 is complete and your local program can be reconstructed in a second empty directory.

Write yourself:

- `pyproject.toml` and `uv.lock`;
- business-rule module;
- input validation;
- file read/write boundary;
- ordinary business tests;
- a one-page product contract covering fields, valid values, missing values, duplicate titles, and state changes.

Do not copy the L10 download or collapsed answer wholesale. Use references only after attempting the work independently.

Exit evidence:

- `environment_recovery`: reconstruct and run in a second empty directory;
- `business_tests`: empty input, zero, invalid input, duplicate titles, unchanged input;
- `failure_recovery`: corrupt JSON or encoding failure preserves old bytes, then repair and rerun.

## V1: Expose the same business behavior through HTTP

Entry condition: V0 passes and you can explain the state changed by every route.

Write yourself:

- FastAPI application entry;
- request and response models;
- route organization;
- configuration loading;
- TestClient tests;
- real Uvicorn request record;
- minimal browser or HTTP-client integration record.

In-memory storage may exist, but the runbook must say that restart loses data and it is not a release version.

Exit evidence:

- `http_contract`: methods, statuses, fields, and error shape;
- `api_tests`: success, 422, 404, PATCH three states, output filtering;
- `real_process_requests`: requests and cleanup on a real port.

## V2: Put state in PostgreSQL

Entry condition: V1 passes and you can explain why memory cannot satisfy restart and concurrency requirements.

Write yourself:

- users/projects/project_members/tasks relationship design;
- SQLAlchemy models;
- Alembic migrations;
- per-request Session and transaction boundary;
- isolated database tests;
- API regressions after replacing storage.

Do not replace migrations with `create_all`, and do not solve existing-data changes by dropping and recreating the database.

Exit evidence:

- `empty_database_migration`;
- `existing_data_migration` with data assertions;
- `transaction_failure_recovery` with no residue after step two fails;
- `isolated_database_tests` with repeatable cleanup.

## V3: Login, object authorization, and idempotency

Entry condition: V2 passes and application/schema compatibility is recorded.

Write yourself:

- controlled account-provisioning command;
- Argon2id password hashing;
- opaque Bearer sessions;
- session digest, expiry, revocation, and authentication version;
- per-request identity reconstruction;
- project-member scoped queries;
- object-level authorization;
- idempotent task-creation receipts.

A request body cannot self-report `user_id`, role, or creator. Hidden frontend buttons and CORS are not authorization.

Exit evidence:

- `identity_lifecycle`: login, password change, disable, logout-all;
- `object_authorization_negative`: Alice cannot read or write Bob's objects even with real IDs;
- `revocation`: an old credential loses object access after membership removal;
- `idempotency_and_retry`: same key/content replay, different-content conflict, and a real race.

## V3.5: Add async only where needed

Entry condition: V3 passes and a real optional external dependency exists.

Write yourself:

- external adapter;
- shared client lifecycle;
- total budget and phase timeouts;
- bounded concurrency;
- response validation;
- cancellation cleanup;
- fault-double tests.

Core CRUD must not depend on external-service success. Do not call `BackgroundTasks` or an in-memory queue a durable task system.

Exit evidence:

- `external_failure_isolation`;
- `cancellation_cleanup`;
- `core_crud_regression`.

## V4: Release to and maintain a real target

Entry condition: V3/V3.5 pass, and you are approved to use the target host, domain, certificate, secret store, database, CI, and notification channel.

Integrate yourself:

- Docker or systemd runtime entry;
- migration identity and application identity;
- Caddy or an equivalent HTTPS entry;
- hosted CI;
- logs, correlation IDs, and alerts;
- backup, isolated restoration, and rollback runbook;
- invited-use scope and maintenance owner.

Local O-stage labs prove mechanisms, not release readiness for your product.

Exit evidence:

- `build_identity`;
- `controlled_migration`;
- `public_https`;
- `logs_and_delivered_alert`;
- `backup_and_isolated_restore`;
- `compatible_rollback`;
- `invited_use_approval`.

## V5: Independent new feature

Entry condition: V4 passes and you have read the G01 scenario catalog.

Implement G01 task comments yourself:

- relationship and interface design;
- migration;
- authorization;
- concurrency and repeated requests;
- release rollback;
- restoration validation;
- human review.

Exit evidence:

- `independent_feature`;
- `feature_release_and_rollback`;
- `feature_restore`;
- `human_review`.

## Pause and resume

At each pause record:

- current stage;
- product revision;
- schema revision;
- last successful command;
- actual failure;
- cleaned-up processes;
- unverified gates;
- one concrete next action.

On resume, first reproduce the last working state. Do not reinstall everything because time passed, and do not delete failure evidence to appear faster.

## Maintenance evidence records

Use `templates/maintenance-record.template` for every dependency/security update, certificate renewal, backup or restore event, incident, access change, user-feedback follow-up, and capacity/cost review. Record the owner, revisions, official sources reviewed, actions, tests, backup/restore evidence, notification evidence, rollback compatibility, unresolved risks, and next review trigger.
