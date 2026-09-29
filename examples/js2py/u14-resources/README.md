# u14-resources

Local CPython 3.13.15 / uv 0.12.13 lab (verified 2026-09-28); pytest 8.4.2. Standard-library business runtime.

Extract the download and enter `u14-resources`. Do not copy `.venv`; reconstruct from the supplied declaration and lock.

```bash
uv sync --locked
uv run --locked python app.py
uv run --locked python -m pytest -q
uv run --locked python -m pytest -q solutions/test_new_report.py
```

Default suite: 12 tests. Reference variation: 2 tests. Write your own implementation from the lesson requirements before opening `solutions`. The default suite does not collect intentional failures in `errors`.

two_yields fails on exit; suppressed intentionally hides an exception and is a counterexample. break does not guarantee close. new_report can retain partial content: closure is not rollback, durability, or crash protection.

Read the matching full lesson for expected outputs, explicit failure commands, mechanism explanations, independent requirements, and limits. All displayed files are canonical files in this archive; no credentials or environments are included. Resume by recording source changes, interpreter/version, working directory, last successful command, observed failure, and the next experiment. Passing this local lab is not a backend deployment certificate.
