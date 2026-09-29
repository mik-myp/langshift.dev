# O01 Operating systems and service processes

Prerequisites: A02 and language/file/dependency/test foundations. Understand cwd, environment, permissions, ports, and stopping before containers. The worker stores a disposable start count, not a complete task API or durable database.

## Environment and restoration

Checked **2026-09-28**. Use an ordinary POSIX account, not root, for permission experiments. CPython **3.13.15**, uv **0.12.13**, pytest **8.4.2**. `.python-version` selects the interpreter, pyproject declares `>=3.13,<3.14`, and uv.lock fixes resolution. `[tool.uv] package=false` means the lab is not built as a distributable Python package.

Repository users run the cd below from the repository root. ZIP users enter the extracted lab root directly, where pyproject.toml resides. `--locked` refuses silent lock changes.

```bash
cd examples/js2py/o01-operating-system
pwd
uv --version
uv sync --locked
uv run --locked python --version
```

The maintainer actually generated the lock using `uv lock --default-index https://pypi.org/simple`. Restoration does not require fresh resolution. Environments/caches are excluded from the allowlist/ZIP; data experiments use owned temporary directories.

## Files and actual commands

worker.py is a single-writer foreground process; --once executes once. process_lab.py owns its children and verifies signals. environment_lab.py makes two cwds and child configuration explicit. permissions_lab.py modifies only temporary files; port_lab.py creates only loopback sockets. Experiments have bounded waits/cleanup and never search for or stop other people’s processes.

```bash
uv run --locked python process_lab.py
uv run --locked python environment_lab.py
uv run --locked python permissions_lab.py
uv run --locked python port_lab.py
uv run --locked python -m pytest -q
uv run --locked python -m solutions.two_directories
uv run --locked python -m pytest -q solutions/test_two_directories.py
```

Key observed output follows. Negative -9 is the POSIX subprocess representation, not an HTTP status or universally identical shell exit.

```text
missing_config_exit=78
SIGTERM: subprocess_returncode=0 cleanup=True
SIGINT: subprocess_returncode=0 cleanup=True
SIGKILL: subprocess_returncode=-9 cleanup=False
same_directory_across_processes=2
[2, 1]
```

## Intentional failures and recovery

Missing/relative OPS_DATA_DIR →78; corrupt JSON, list root or boolean starts →65; an owned unwritable directory →74; wrong cwd →FileNotFoundError; a second bind is refused; SIGKILL skips cleanup. Tests verify these failures without converting them into business success. Do not hide permission faults with sudo/chmod777. Starting with a new owned temporary directory is lab recovery, not permission to discard a real database.

## Manual worker and stopping

For manual use, prepare a directory dedicated to this lab, supply its absolute path through OPS_DATA_DIR, and launch worker.py. It waits after ready; Ctrl+C in that terminal requests normal SIGINT stopping. Automatic scripts clean up their own Popen child and need no additional kill. Never claim finally always runs without considering forced termination.

## Linux/systemd (not executed)

The complete unit is systemd/ops-worker.service. A target administrator first checks for conflicting services/accounts, provisions a dedicated non-login langshift-ops account/group on a rebuildable Linux host, deploys source to /opt/langshift/o01-operating-system, and restores .venv there. The service account reads/executes but cannot modify source. StateDirectory supplies /var/lib/langshift-ops. Do not copy a macOS venv or rehearse on production. Review/validate the unit, then install it at /etc/systemd/system/ops-worker.service only with approval. The commands below are pending acceptance after provisioning, not a success log.

```bash
systemd-analyze verify systemd/ops-worker.service
sudo systemctl daemon-reload
sudo systemctl start ops-worker.service
sudo systemctl status ops-worker.service --no-pager
sudo journalctl -u ops-worker.service -n 30 --no-pager
sudo systemctl stop ops-worker.service
```

## Independent requirement

From requirements alone: create first/second roots, run first twice and second once, deliberately give every child cwd=second, and obtain [2,1] without shared parent memory. Clean up only owned resources even on failure. Reference solutions/two_directories.py and its separate test after attempting the task. Explain SIGTERM versus SIGKILL, permission recovery, and pending Linux acceptance.

## Environment matrix (machine-readable: ENVIRONMENT.json)

| State | Evidence / gate |
| --- | --- |
| actually_run | CPython3.13.15 on Darwin25.6.0 arm64 ordinary uid501; env/cwd and missing-file failure; SIGTERM/SIGINT cleanup, SIGKILL absence of cleanup; nonroot mode denial/restoration; loopback bind collision and owned socket cleanup; configuration78/data65/I-O74 failures; two independent data roots |
| unavailable_here | Linux/systemd runtime and service account provisioning |
| user_must_supply | rebuildable controlled Linux/systemd host; dedicated service account/group and reviewed deployment directories; administrator approval for installing a system unit |
| pending_acceptance | systemd-analyze verify on target; real unit start/stop/restart and effective filesystem restrictions; boot lifecycle if enabled; Windows semantics and power-loss/concurrent persistence are outside acceptance |

This run passed **16 standard** and **1 independent** cases. Source/text are `implemented`; external environment gates remain `environment_pending`, not deployment acceptance. Ordinary macOS tests do not replace Linux/container/public or Windows evidence.

## Resume and diagnosis record

Record source/lock hashes, cwd, tool versions, last successful command, failure stage/category, actual case counts, environment matrix, and next first step. Never record a full environment, real token, database URL, or private key. Resume with `uv sync --locked`, standard tests, and your own independent tests. A passing reference alone does not establish independent ability.

## Primary sources

SOURCES.json records official URLs, scope, HTTP retrieval results and SHA-256 digests checked on 2026-09-28. The chapter explains mechanisms; this README provides the offline execution entry. No production resource creation, system-software installation, or acceptance of service terms is automated here.
