# Verification record — s03-reliable-operations

核验 / Executed **2026-09-28**, macOS arm64. This is local evidence, not a
production security audit or proof that untested integrations are safe.

## Executed source-tree acceptance

```bash
export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
export UV_PYTHON_INSTALL_DIR=/tmp/langshift-js2py-python-20260928
export UV_CACHE_DIR=/tmp/langshift-js2py-uv-cache-20260928
uv sync --locked
uv run --locked python -m pytest -q
```

Working directory: this lab root. The repository convenience runner is
`scripts/test-js2py-security-foundations.py`; shared test registration was not
edited. CPython3.13.15 / uv0.12.13 / PostgreSQL18.6; complete dependency pins are
in pyproject.toml and real public-PyPI uv.lock.

- **58 passed**, not merely compiled or imported.
- The fixture recorded **315 real loopback HTTP responses**. Status
  distribution: `{200: 132, 201: 98, 204: 8, 401: 21, 403: 5, 404: 21, 409: 4, 422: 24, 503: 2}`.
  This count excludes three additional real client.py subprocess requests
  (login, me, password change) whose outputs/private-file behavior were asserted.
- A fresh owned mkdtemp PostgreSQL cluster, private Unix socket, no TCP listening;
  server_version_num=180006 and READ COMMITTED were asserted.
- API process exited with 0; the owned cluster was stopped and its
  temporary root was confirmed absent after the run. No existing DB was selected.
- API and owned PostgreSQL restart tests verify committed state survives. Helper
  stop deliberately deletes the lab cluster and is not a persistence test.
- Application credential log scan: PASS. PostgreSQL credential log scan: PASS.
  No test credential values are published in this file or retained handoff evidence.

## Sensitive validation and error checks

Actual HTTP probes cover password too long, wrong JSON type, nested password value,
current/new password errors, short new password, malformed JSON and a secret marker
used as an unknown JSON field name. Returned errors retain only sanitized loc/type,
not input/ctx/msg/body or the unknown key. Tests check generic unknown-account,
wrong-password and disabled-account401, malformed/altered/expired Bearer401,
WWW-Authenticate, and token response no-store.

A real ALTER TABLE on the fixture-owned auth_sessions forces a database error:
GET /users/me returns generic503 without SQL/driver/credential details. The test
restores the table in finally and gets200 with the same still-valid token. A
wrong migration revision yields live200/ready503, then ready200 after restoration.
Private-client tests verify mode0600, refusal of a group/world-readable file,
getpass-based account creation and login/password-change output without secrets.

Application and PostgreSQL logs are scanned after process shutdown for generated
passwords, successful/altered Bearers and injected marker strings. Access logs are
disabled; audit records fixed events and server actor IDs only. SQL parameter
hiding is not treated as sufficient to sanitize driver messages; expected SQL
failures have explicit sanitized handlers. These probes are not a guarantee about
arbitrary new logging paths, every unknown exception, proxies or APM.

## Real revocation ordering

Two distinct PostgreSQL connections prove that disabling waits while an earlier
authenticated operation holds its shared user lock. pg_blocking_pids confirms an
actual wait, not a sleep-only guess. After the earlier transaction and disable
commit, the old credential gets401. Already-authorized work may finish; responses
already started cannot be retroactively canceled. Password changes/logout-all
increment auth_version; disable then enable does not revive old sessions.

## Object authorization and migration evidence

Known Bob project/task IDs are given to Alice. Outsider lists omit them; direct
reads, writes, deletes and task-under-wrong-parent access are denied404. Membership
allows reads but not editing another creator's task403. Request bodies cannot
self-assign role/owner_id/created_by. Current membership is required even for a
historical task creator. Owner deletion409; removal204 followed by me200 and
object404. Project+owner insertion rolls back both on a real second-step FK failure.
Duplicate invitation409 does not poison the next request. Project deletion removes
children atomically. Multiple legacy owners block005 without silent repair; D
priority/task records survive, and legacy users get no default password.

A second two-connection test holds a project writer's shared lock while owner
removal waits; distinct backend PIDs and pg_blocking_pids prove ordering. The prior
write commits, removal commits, Alice gets404 and owner200. This covers declared
project operations, not retroactive cancellation of already-started responses.
Global project lists are scoped statement snapshots, not per-project-locked or
items/total-consistent snapshots. Concurrent invitation versus account disabling
is not promised to be atomic. Extra body keys and sensitive path/query values are
also checked for response and application/PostgreSQL log echo.

## Idempotency and real unique-index contention

Real HTTP verifies first201/replay201 with equal ID and false/true replay headers,
one task/one receipt, changed-payload409, missing/noncanonical key422, scoped keys,
UTC/default normalization, and historical rather than live response replay.
Permission/version checks occur before replay: removed member404, revoked token401.
A precommit fault rolls back task and provisional receipt together.

Two simultaneous HTTP calls converge. Three separately controlled two-connection
races record different backend PIDs and actual unique-index wait relationships:

| First transaction | Contender payload | Contender | Committed task count |
| --- | --- | --- | --- |
| Commit | Same | Replay201 | 1 |
| Commit | Different | 409 | 1 |
| Rollback | Same | Creates201 | 1 |

READ COMMITTED is asserted and the loser reads the winner in a new statement.
Sequence gaps after rollback are allowed. Committed receipts survive API and owned
PG restarts. An expired retained receipt gives409; explicit purge removes it and
reuse can create another task, deliberately proving the deduplication limit.
Decimal/UTC variation tests are unit checks, not counted as real HTTP acceptance.


## Final isolated-copy and actual CLI repetition

The final executable sources were copied from `s03-reliable-operations-files.json` into a fresh
allowlist-only directory (no .venv/session/cache/PGdata copied). The isolated
repository runner installed a new .venv and passed the same **58 cases**.
Across the three labs: **123 source-tree cases + 123 clean-copy cases**. A separate
`JS2PY_LAB_ROOT` single-extracted-root run passed **22 S01 cases**. These are
repeated executions, not 268 globally distinct test implementations.

```bash
python3 scripts/test-js2py-security-foundations.py --lab-root /path/to/extracted-parent --evidence-dir /path/to/redacted-evidence
JS2PY_LAB_ROOT=/path/to/extracted-single-lab python3 scripts/test-js2py-security-foundations.py --lab s03-reliable-operations
```

During the clean run, VIRTUAL_ENV/UV_PROJECT_ENVIRONMENT pointed to an owned decoy,
UV_ACTIVE/UV_PYTHON/UV_CONFIG_FILE were deliberately invalid, UV_NO_CONFIG was
false, and PGHOSTADDR/PGSERVICE/PGDATABASE plus pytest argument/plugin overrides
were injected. The runner removed them, set no-config and explicit Python3.13.15,
retained only controlled Python/cache paths, and left the decoy sentinel directory
unchanged. It supports both `--lab-root` and `JS2PY_LAB_ROOT`, and refuses a .venv
symlink. It does not edit shared download/test registrations.

This lab also completed **18 actual client.py HTTP requests** from its clean copy,
using the default app entry (not just the solution entry used in pytest). Actual
labdb.py start/status-export/restart/stop were exercised with injected PG defaults.
API port conflict affected only the second owned process; the original remained
healthy. API and PG restarts retained committed state; final owned cleanup passed.
The three manual worksheets recorded **54 client requests** in total, separately
from pytest's recorded API requests and readiness polling.

## Independent-audit finding repaired and regressed

The read-only audit's P2 `SEC-S01-S03-001` correctly found that a loopback URL did
not prevent urllib's default environment proxy from receiving credentials. All
three clients now use `build_opener(ProxyHandler({}), NoRedirect())`. The fixture
HTTP client disables inherited proxies too. The new regression uses only owned
127.0.0.1 proxy, target and redirect listeners and synthetic credentials, with
proxy settings present and no_proxy absent: **target3 / proxy0 / redirect-target0**.
It asserts the target received the synthetic password/Bearer but writes no values
to evidence. No real proxy or personal credential is involved.

The separate libpq-isolation regression injects PGHOSTADDR/PGHOST/PGPORT/PGSERVICE/
PGSERVICEFILE/PGUSER/PGDATABASE/PGPASSWORD/PGOPTIONS, then successfully starts,
restarts and removes an owned PostgreSQL cluster. isolation.py clears PG* before
process/fixture connections; DB tools use a cleaned child environment. db.py and
migration env.py apply the same boundary for their independent CLI processes.

Final canonical files changed after the earlier read-only audit. The handoff
provides SHA-256 for every deliverable and a diff against the auditor's end
manifest. This is author regression evidence, **not a claim that an independent
review has already approved every final hash**. Core policy/transaction algorithms
were not rewritten by this fix. Shared-site build and TypeSafe remain owner work.

## Exclusions and integration boundary

Not verified: production TLS, login/body/rate limits, Argon2 load capacity,
compromised-password screening, public signup/recovery/MFA, cookie/CSRF design,
external logging/APM and every unknown exception, distributed clock skew,
production backup restore, RLS, ownership transfer, all deadlock/cleanup
interleavings, cross-service effects or exactly-once delivery. A readiness response
is not proof of these properties. Auth digests, password hashes and receipt data
still require controlled database/backup access.

The nine chapter locales are checked independently with installed MDX3/GFM and
React server rendering using in-memory loader substitution, plus exact ordered
code/source parity. That proves isolated document syntax/rendering, not shared
loader integration, Code Hike/site build, download ZIP generation or API correctness.
The owner integrates shared loaders/manifests/ZIPs/navigation/test registration.
No frontend dependency, API key, TypeSafe call, subagent or git commit was used.
