# u11-typing

Local CPython 3.13.15 / uv 0.12.13 lab (verified 2026-09-28); pytest 8.4.2; mypy 2.3.1. Standard-library business runtime.

Extract the download and enter `u11-typing`. Do not copy `.venv`; reconstruct from the supplied declaration and lock.

```bash
uv sync --locked
uv run --locked python -m mypy
uv run --locked python app.py
uv run --locked python -m pytest -q
uv run --locked python -m pytest -q solutions/test_first_over.py
```

Default suite: 8 tests. Reference variation: 2 tests. Write your own implementation from the lesson requirements before opening `solutions`. The default suite does not collect intentional failures in `errors`.

Static rejection differs from runtime failure. annotation_only prints 33; bool_static passes mypy but fails runtime rules. unchecked deliberately demonstrates unchecked bodies.

Read the matching full lesson for expected outputs, explicit failure commands, mechanism explanations, independent requirements, and limits. All displayed files are canonical files in this archive; no credentials or environments are included. Resume by recording source changes, interpreter/version, working directory, last successful command, observed failure, and the next experiment. Passing this local lab is not a backend deployment certificate.
