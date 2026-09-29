# js2py 00 — your first Python script / 第一个 Python 脚本 / 第一個 Python 腳本

This is a **single-script lesson**, not a configured application project.
There are no third-party Python dependencies, lockfiles, test frameworks, or
application servers to understand or install. The full lesson explains every
line before asking you to change it.

## Run / 运行 / 執行

Install uv from its official documentation if needed:
https://docs.astral.sh/uv/getting-started/installation/

In a normal terminal, enter the extracted `u00-first-script` directory. Use the
course's Python 3.13 baseline; it is not a claim about the latest Python version.

```sh
uv python install 3.13
uv run --no-project --python 3.13 python --version
uv run --no-project --python 3.13 python first_steps.py
```

The first two commands prepare/identify the interpreter. The last command runs
`first_steps.py` without discovering a parent uv project. All uv invocations
require the uv tool; only initial installation/download needs network access if
that interpreter is not already available. The Python program itself has no
network behavior. Installation and diagnostic messages are not program output.

Expected program output:

```text
Hello!
Python
```

You may instead use an already configured Python 3.13 interpreter directly. The
lesson fixes one command path so interpreter ambiguity is not a learning task.

## Exercises / 练习 / 練習

1. Explain why `print(course)` prints the value but `print("course")` prints the
   literal word. Change just that line, predict the output, then restore it.
2. Change `course` from `"Python"` to `"FastAPI"`; predict both output lines.
   Changing text does **not** install FastAPI or start a web server.
3. Create `about_me.py` beside `first_steps.py`. Assign `"Python"` to `subject`,
   print `"My next skill:"`, print the value of `subject`, reassign it to
   `"FastAPI"`, then print its new value. Do not add imports, functions or tools.

```sh
uv run --no-project --python 3.13 python about_me.py
```

Expected exercise output:

```text
My next skill:
Python
FastAPI
```

Only after trying the task, compare with `solutions/about_me.py`. You do not need
to run or understand a test suite to finish this chapter.

## Failure experiments / 排错 / 排錯

Work in a copy and restore after each experiment. With the rest of the original
file unchanged:

- Replace `print(course)` with `print(cours)`: `Hello!` is printed before a
  `NameError`. The name on line 3 has not been assigned.
- Remove the closing quote in the first line: `SyntaxError`; none of the file's
  print statements executes. Restore the quote before investigating anything else.

A wrong directory or filename is a different problem: the interpreter cannot
open the requested file. Follow the full lesson for locating the right folder.

## Scope / 边界 / 邊界

Understand, modify, and debug this script before proceeding to Python values
and names. Virtual environments, dependency locking, imports, pytest, and the
independent reproducible application have their own later chapters.

Maintainer regression tests live outside this learner download and are not
additional student prerequisites.
