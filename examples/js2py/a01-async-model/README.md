# A01 — Python async execution

Verified 2026-09-28. This is an independent local lab following S03, not the full
capstone. No other chapter source is imported. Prerequisites: Python functions,
exceptions, context managers, tests and the existing synchronous API/SQL/auth
foundations. A02 additionally builds on A01, L14 and H05.

## Reproduce from a clean download

Extract and enter `a01-async-model`. In the repository, enter `examples/js2py/a01-async-model`.
Use CPython 3.13.15, uv 0.12.13, pytest 8.4.2. Install the specified uv first;
its installation is not performed by this lab. No third-party runtime dependency.
The web baseline follows H03–H06; the lifecycle dependencies follow H05–H06.
The actual public-PyPI lock includes artifact hashes. `requires-python` accepts
3.13 only and `tool.uv.package=false` runs local source without packaging it.
Do not delete the lock or replace the baseline with an unreviewed upgrade.

```bash
# Run from the extracted a01-async-model directory.
set -eu
export PATH="$HOME/.local/bin:$PATH"
export UV_PYTHON_INSTALL_DIR=/tmp/langshift-js2py-python-20260928
export UV_CACHE_DIR=/tmp/langshift-js2py-uv-cache-20260928
uv --version
uv python install 3.13.15
uv sync --locked
uv run --locked python --version
uv run --locked python app.py
uv run --locked python -m pytest -q
uv run --locked python -m pytest -q solutions
```

These `/tmp` locations isolate the verified interpreter/download cache. They
contain no application data. Network is needed to install locked public packages,
but running the lab never calls a paid/third-party service or uploads user data.

## Stable demo transcript

The source of this transcript is `expected-output.txt`; execution must match it.

```text
creation: called:no-body-yet | A:start | A:end
sequential: A:start | A:end | B:start | B:end
scheduled: A:start | B:start | owner:both-entered | B:end | A:end
blocking: sync:start | sync:end | callback:ran | owner:resumed
offloaded: loop:responsive-while-thread-waits | thread:returned
cancelled: file:opened | file:closed | owner:cancelled
timeout: file:opened | file:closed | owner:timeout
bounded: peak=2 active=0
```

Main tests: **19 passed**. Independent reference tests: **5 passed**.
Elapsed time is intentionally not a correctness assertion. Python warnings are
errors except in the deliberately captured warning diagnostic. Main tests do not
silently include answer tests; run both commands.

## File map and interpretation

- `comparison.py` / `comparison.js`: complete Python/JS call-before-body comparison.
- `scheduling.py`: creation, sequential awaiting, explicit scheduling, blocking, and a joined thread bridge.
- `ownership.py`: cancellation/deadline cleanup with real temporary files.
- `capacity.py`: bounded admission proved with entered/release gates.
- `app.py`: the complete stable demo above.
- `tests/test_model.py`: ordered events, file closure/rejected writes, permit reuse and actual failure commands.
- `solutions/batch.py` / `solutions/test_batch.py`: an independent, bounded, cancellable batch.

The JS comparison optionally uses your existing Node installation:

```bash
node comparison.js
uv run --locked python comparison.py
```

The expected transcripts are `expected-javascript.txt` and `expected-python.txt`.
Python coroutine calls do not start their bodies. Default-factory Tasks explicitly
schedule work. Direct awaits are sequential; an await on an already-ready object
need not suspend. Do not infer event-loop progress from elapsed-time guesses.

## Actual failures and exercises

`uv run --locked python errors/reuse.py` prints 42 then exits 1 with RuntimeError.
`uv run --locked python errors/forgotten.py` captures a real never-awaited warning;
the work's events remain empty. `uv run --locked python errors/swallow.py` exits 0
but shows pretend-success and cancelled=False: a semantic failure, not success.
The suite checks these commands in fresh subprocesses.

Guided change: limits 1 and 3, verifying peak and zero active work rather than timing.
Independent change: normalize all inputs before side effects, allow at most eight
items, preserve result order, bound concurrency/deadline, and drain all children on
error/timeout/cancellation. Reference tests include no-surviving-child assertions.
Input-order observation is not fail-fast sibling supervision.

Recovery card: current file, Python/uv versions, last successful command, which 19+5
tests passed, your changed condition, first counterexample, next focused command.
Do not repair ordering by increasing arbitrary sleeps. Restore only this lab's own
files; do not delete unrelated environments or alter shared repository configuration.

## Safety and limitations

This lab opens temporary files and one explicitly joined local worker thread. It
contacts no service and needs no credentials. Cancellation cannot forcibly stop a
thread or undo completed effects. A blocked loop cannot enforce a strict wall-clock
deadline. The semaphore limits admitted work, not an unlimited number of allocated
Tasks. No throughput, production queue, async database or deployment claim is made.

## Download/source contract

`DOWNLOAD-ALLOWLIST.json` mirrors the repository's same-named-lab `-files.json` list.
Only those regular files may be archived. Environments, caches, credentials and real
business data are excluded. The site loader reads the same files shown in the chapter.
`sources.json` records official source URLs and the verification date. Package hashes
are supplied by public PyPI in uv.lock, not fabricated by a packaging script.
