# js2py: retained engineering-stage project (formerly U00)

This is retained material for a later engineering stage, **not the current
chapter 00 prerequisite or required download**. Learn functions, containers,
modules, files and basic tests before using it; the fixture/subprocess cases
need additional test concepts. Its historical path remains for compatibility.

It is a local program, **not a FastAPI server**, and deliberately trusts the supplied JSON
fixture. It does not validate arbitrary user input or implement persistence.

## Run / 运行 / 執行

Install uv using its official installation instructions, then open a terminal
in the extracted project directory. The course uses CPython 3.13; uv can install
that interpreter when it is not already available.

```sh
uv sync --locked
uv run --locked python main.py
uv run --locked python -m pytest -q
uv run --locked ruff check .
uv run --locked ruff format --check .
```

Expected application output:

```text
Tasks: 3 | Done: 1 | Pending: 2
```

The default test suite has six cases. It includes execution from another working
directory and importing the module without running the program.

## Exercise / 练习 / 練習

Implement `next_task_title(tasks)` in `next_task.py`:

- Return the title of the first task whose `done` value is `False`.
- Return `No pending tasks` for an empty or fully completed list.
- Do not mutate the list or its dictionaries.

```sh
uv run --locked python -m pytest exercises/test_next_task.py -q
```

**The starter intentionally fails these four exercise cases.** They are not part
of the default test suite. Do not rewrite the tests to make the starter pass.
The separately stored reference answer is in `solutions/next_task.py`.

## Reproducibility / 环境复现 / 環境重現

Commit source files, `pyproject.toml`, `.python-version`, and `uv.lock`.
Do not commit `.venv`, caches, real secrets, or `.env`.
`uv sync --locked` checks that the manifest and lockfile agree; it does not update
the lockfile to hide a mismatch. A lockfile fixes dependency resolution, not the
entire operating system or every platform-specific behavior.

The previous three-language lesson is preserved in
`docs/archive/js2py-u00-engineering` as authoring material. Its old introductory
mastery gate is superseded; it is not the current published chapter 00.
