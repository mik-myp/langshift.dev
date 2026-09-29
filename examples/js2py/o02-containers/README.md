# O02 Containers and deployable applications

Prerequisites: O01/L08. This health-only smoke app has no tasks, authentication, authorization, or database and cannot serve real users. Dockerfile/Compose and a scoped runner are provided, but no engine exists here: real build/execution remain pending.

## Environment and restoration

Checked **2026-09-28**. Use an ordinary POSIX account, not root, for permission experiments. CPython **3.13.15**, uv **0.12.13**, pytest **8.4.2**. `.python-version` selects the interpreter, pyproject declares `>=3.13,<3.14`, and uv.lock fixes resolution. `[tool.uv] package=false` means the lab is not built as a distributable Python package.

Web baseline: FastAPI **0.135.1**, Uvicorn **0.42.0**, Pydantic **2.12.5**, HTTPX **0.28.1**, Starlette **0.52.1**, AnyIO **4.12.1**. No frontend dependencies.

Repository users run the cd below from the repository root. ZIP users enter the extracted lab root directly, where pyproject.toml resides. `--locked` refuses silent lock changes.

```bash
cd examples/js2py/o02-containers
pwd
uv --version
uv sync --locked
uv run --locked python --version
```

The maintainer actually generated the lock using `uv lock --default-index https://pypi.org/simple`. Restoration does not require fresh resolution. Environments/caches are excluded from the allowlist/ZIP; data experiments use owned temporary directories.

## Locally executable checks

local_probe.py owns a loopback Uvicorn child. With an unwritable directory, live stays200 and ready becomes503; recovery restores ready200; /tasks is404. check_config checks selected invariants, not full Docker/Compose parsing. secret_demo uses a fictional marker and never outputs its value.

```bash
uv run --locked python check_config.py
uv run --locked python local_probe.py
uv run --locked python secret_demo.py
uv run --locked python -m pytest -q
uv run --locked python -m pytest -q solutions/test_restore_copy.py
uv run --locked python container_probe.py
```

```text
host_http_live=200
host_http_ready=200
unwritable_live=200
unwritable_ready=503
restored_ready=200
tasks_not_implemented=404
container_runtime=NOT_VERIFIED
```

Without explicit opt-in, container_probe exits77 with environment_pending, not a container pass. Standard14 and independent3 cases were executed. Ordinary-file restoration and real container-volume verification are separate evidence.

## Build and runtime boundaries

The two-stage Dockerfile restores locked production dependencies and runs as10001. .dockerignore denies everything then permits nine build files. Select compose.json explicitly with -f. Host publication is127.0.0.1:8033; internal listening is0.0.0.0:8000. These are different network namespaces. Read-only root, /data named volume, /tmp temporary space and least privilege are explicit. Healthcheck reports readiness; it neither proves authorization nor automatically restarts an unhealthy container.

OPS_DATA_DIR is not a secret. Passwords/tokens must not enter image layers, ARG/ENV, command lines, logs or downloads; secret_demo is not production secret management. Base-tag availability/digest/architecture remain engine-unverified. Volumes are not backups. Same-container stop/start retains the writable layer; recreation does not inherit it automatically.

## Commands after supplying a controlled engine (unexecuted)

Read container_probe.py first. Require Linux Docker Engine>=28, an explicit local UNIX socket, and permission for image download. Never use a remote TCP/SSH endpoint or default context. The runner removes Docker environment selection and uses empty temporary configuration instead of credential helpers. Unique names scope removal to its own containers/volume/image, with no global prune; base images/build cache may remain. Actual output must come from your target environment.

```bash
uv run --locked python container_probe.py --socket /path/to/controlled/docker.sock --confirm-controlled-engine
```

The runner checks UID, read-only root, host binding, health, named-volume recreation=1, same unmounted instance stop/start=1, and fresh unmounted recreation=0. Do not kill user processes after port conflicts or chmod real data777 after permission errors. Preserve build-stage evidence rather than switching to latest to bypass the version contract.

## Independent requirement

Copy a quiescent teaching counter into a new empty directory and read the same value. Reject nonempty destinations and corrupt sources without altering original state. solutions/restore_copy.py and three tests are references. Ordinary file copying is not a live PostgreSQL backup.

## Environment matrix (machine-readable: ENVIRONMENT.json)

| State | Evidence / gate |
| --- | --- |
| actually_run | selected Dockerfile/.dockerignore/Compose text and JSON invariants; real owned loopback Uvicorn HTTP200/503/recovery/404; nonroot host permission failure; fictional0600 secret marker without value output; single-writer file lifecycle and independent empty-directory restore; unopted container runner exits77 environment_pending |
| unavailable_here | Docker/OrbStack/Podman/Apple container/nerdctl/Colima/Lima CLI, common apps/sockets not found; no controlled Linux container engine |
| user_must_supply | controlled local Linux Docker Engine>=28; explicit verified local UNIX engine socket; no remote context; permission/network/storage for registry base-image download and build |
| pending_acceptance | base-image tag availability, digest, target architecture and build; real Compose parser; container uid10001/read-only root and host loopback publication; named-volume ownership, health and stop/start/removal/recreation; container_probe real-engine branch and scoped cleanup; full capstone/auth/DB integration; this is health-only |

This run passed **14 standard** and **3 independent** cases. Source/text are `implemented`; external environment gates remain `environment_pending`, not deployment acceptance. Ordinary macOS tests do not replace Linux/container/public or Windows evidence.

## Resume and diagnosis record

Record source/lock hashes, cwd, tool versions, last successful command, failure stage/category, actual case counts, environment matrix, and next first step. Never record a full environment, real token, database URL, or private key. Resume with `uv sync --locked`, standard tests, and your own independent tests. A passing reference alone does not establish independent ability.

## Primary sources

SOURCES.json records official URLs, scope, HTTP retrieval results and SHA-256 digests checked on 2026-09-28. The chapter explains mechanisms; this README provides the offline execution entry. No production resource creation, system-software installation, or acceptance of service terms is automated here.
