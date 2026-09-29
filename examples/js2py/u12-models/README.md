# u12-models

Local CPython 3.13.15 / uv 0.12.13 lab (verified 2026-09-28); pytest 8.4.2. Standard-library business runtime.

Extract the download and enter `u12-models`. Do not copy `.venv`; reconstruct from the supplied declaration and lock.

```bash
uv sync --locked
uv run --locked python app.py
uv run --locked python -m pytest -q
uv run --locked python -m pytest -q solutions/test_work_log.py
```

Default suite: 9 tests. Reference variation: 2 tests. Write your own implementation from the lesson requirements before opening `solutions`. The default suite does not collect intentional failures in `errors`.

shared_state silently shares a list; missing_self raises TypeError; no_validation demonstrates that RawEstimate does not validate. Public mutation can still bypass initialization rules.

Read the matching full lesson for expected outputs, explicit failure commands, mechanism explanations, independent requirements, and limits. All displayed files are canonical files in this archive; no credentials or environments are included. Resume by recording source changes, interpreter/version, working directory, last successful command, observed failure, and the next experiment. Passing this local lab is not a backend deployment certificate.
