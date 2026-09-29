# L04 — 函数、参数与作用域 / Functions, Parameters, and Scope

前置知识／先修知識：L00–L03。先能解释容器、引用和控制流，再抽取函数。
Prerequisites: L00–L03. No imports, annotations, exception handlers, classes,
decorators, asynchronous work, or project configuration are required.

## Run a standalone example

Extract the ZIP and open `u04-functions` in your editor and terminal. Use the
CPython 3.13 teaching baseline; this is not a claim that it is the latest release.
Each file runs as an independent process without state from earlier examples.

```sh
uv run --no-project --python 3.13 python definition_and_call.py
```

Replace only the final filename for another example. No third-party Python
packages are needed. Return to L00 for environment troubleshooting. The actual
verification interpreter version is recorded in the implementation log.

## Teaching order

1. `definition_and_call.py`: executing def versus executing a call.
2. `return_paths.py`: early return, implicit None, bare return, print side effects.
3. `arguments.py`, `keyword_only.py`: positional/keyword binding and named options.
4. `argument_binding.py`: local rebinding versus mutation of shared arguments.
5. `default_values.py`, `pitfalls/shared_default.py`, `fresh_defaults.py`:
   definition-time defaults, accidental reuse, per-call creation and explicit copying.
6. `local_scope.py`: call-local names and runtime lookup of a top-level name.
7. `function_values.py`: pass a function rather than one call's result.
8. `closure_factory.py`, `closure_binding.py`: configuration factories and binding
   lookup, not a definition-time value snapshot.
9. `task_rules.py`: classify one estimate, build a fresh report, display at the caller.
10. Attempt the exercises before opening `solutions/`.

The web chapter supplies explanations, state relationships, expected output,
syntax-error experiments, input variations, three checkpoints and closed answers.
It does not require learning all signature forms at once.

## Eight expected failures

| File | Expected exception | Failing line |
| --- | --- | --- |
| `errors/before_definition.py` | NameError | 1 |
| `errors/missing_argument.py` | TypeError | 6 |
| `errors/duplicate_argument.py` | TypeError | 6 |
| `errors/unknown_keyword.py` | TypeError | 6 |
| `errors/positional_option.py` | TypeError | 8 |
| `errors/printed_result.py` | TypeError after printing 25 | 6 |
| `errors/local_before_binding.py` | UnboundLocalError inside the called function | 5 |
| `errors/not_callable.py` | TypeError attempting to call a bool | 7 |

Except for printed_result.py, these files produce no standard output before
failing. Binding failures must not print the Body ran marker. The shared-default
pitfall exits successfully but changes the previously returned list on a later
call. Exit status alone is not the learning outcome.

The chapter's deliberately invalid positional-after-keyword fence is not included
as a downloadable .py file. The download contains valid-syntax scripts, including
the eight expected runtime failures above.

## Independent acceptance / 独立验收／獨立驗收

从空文件建立自己的 `study_rules.py`，不要先复制参考答案。实现创建任务、资格判断、
按传入规则选择和预算规则工厂；在调用方显示结果，四个函数内部不打印。
先完成預測、修復與輸入變式，再檢查 `solutions/study_rules.py`。

```sh
uv run --no-project --python 3.13 python study_rules.py
```

Expected original output:

```text
['python']
['python', 'review']
['python']
False
Within 20: ['Read', 'Zero']
Within 40: ['Read', 'Practice', 'Zero']
False
Source tasks: 6
```

Verify empty and all-completed inputs, zero budget, the exact budget boundary,
repeated construction with omitted tags, explicit empty-list isolation, repeated
alternating rules, and intentional sharing of selected task dictionaries. Empty
selection must not invoke the rule. No hard-coded output or hidden global state.

Contracts are bounded: titles/tags are strings; done is bool; estimates are None,
integers excluding bool, or missing when checked; budgets are nonnegative
integers. This is not arbitrary external-input validation or a backend service.

Pause with the filename, last arguments, returned value, printed output, input
mutation, unresolved binding relationship and the next first step. No fixed
weekly schedule is assumed.

## Maintainer checks (not learner prerequisites)

Run from the repository root with the existing tools:

```sh
python3 scripts/build-js2py-lab.py --lab u04-functions
python3 -m unittest discover -s scripts/tests -p test_js2py_functions.py -v
python3 scripts/test-js2py-functions.py
```

The integration requires uv and Python 3.13, extracts the actual ZIP, checks all
expected behaviors, runs from an empty folder, and proves that an incompatible
parent project is ignored without modifying its files.

The deliberately broken before_definition.py and local_before_binding.py also
trigger static Ruff F821 and F823 diagnostics. Maintainer lint runs exempt only
those specific codes on those two exact files. Their runtime errors remain tested;
this is not permission to suppress errors across the lesson. No learner needs
Ruff to run these examples.
