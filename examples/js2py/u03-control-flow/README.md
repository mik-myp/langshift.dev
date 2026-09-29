# L03 — 条件、循环与遍历 / Conditions, Loops, and Traversal

适用：已完成 L00–L02 的读者；不要求函数定义、导入、异常捕获或项目配置。
Prerequisites: L00–L02; no function definitions, imports, exception handlers, or project setup.

## Run one independent file

Extract the download, open `u03-control-flow` in the editor, and use a terminal in
that folder. The teaching baseline is CPython 3.13. The actual maintainer
verification version is recorded in the implementation log; this is not a claim
that 3.13 is the latest Python release.

```sh
uv run --no-project --python 3.13 python branches.py
```

Change only the final filename for the other examples. No third-party Python
packages are needed. Each file is a fresh, independent program, not a notebook
cell depending on previous state. `--no-project` keeps parent project metadata
out of this lesson. Return to L00 if the command cannot run.

## Read in teaching order

1. `branches.py`: mutually exclusive branches, boundary values, indentation.
2. `truthiness.py`, `logical.py`: empty values, short circuits, preserving zero.
3. `for_tasks.py`, `loop_binding.py`: accumulators and reference/name behavior.
4. `ranges.py`: excluded stop, direction, and empty ranges.
5. `unpacking.py`, `numbered_tasks.py`: unpack before learning enumerate.
6. `dict_iteration.py`: keys versus items, not implicit JS-style destructuring.
7. `while_budget.py`: explicit progress and termination; 0/1/20/21 boundaries.
8. `loop_controls.py`: skip completed entries and stop at the first match.
9. `pitfalls/mutation_skip.py`, `safe_filter.py`: reproduce a silent bug, then repair.
10. `comprehensions.py`: compare an understood ordinary loop with its shorter form.
11. `task_summary.py`: variable-sized and empty task collections, guarded division.
12. Attempt the independent exercises before opening `solutions/`.

The three `errors/` files intentionally exit unsuccessfully:

| File | Expected failure | Line |
| --- | --- | --- |
| `errors/empty_loop.py` | NameError after zero loop iterations | 4 |
| `errors/zero_step.py` | ValueError constructing a zero-step range | 1 |
| `errors/unpack_pair.py` | ValueError unpacking three items into two targets | 2 |

These files should produce no standard output before failing. The lesson also
has a clearly marked, separate indentation syntax-error experiment; it is not
included among downloadable valid-syntax files. The `pitfalls/` example exits
successfully but wrongly leaves a completed task in the list. Exit status alone
is not a correctness test. No downloadable file deliberately runs forever.

## Independent acceptance / 独立验收

先从空文件创建自己的 `study_queue.py`，按网页需求写队列报告，再查看
`solutions/study_queue.py`。预算按每一项独立比较，不是累计扣减。0 是合法时长；
缺失与 None 在本题明确合并为 unknown；负数单独记为 invalid；已完成项不参加
待办时长计算。不得修改源 tasks，也不得硬编码计算结果。

```sh
uv run --no-project --python 3.13 python study_queue.py
```

Original expected output:

```text
Tasks: 6; pending: 5
Known pending time: 20 minutes
Unknown: 2; invalid: 1
Ready within 20 minutes each: 2
1. Read branches
2. Try empty input
```

Change inputs, not the processing logic: empty input; all completed; budget zero;
21-minute first task; a previously missing estimate set to five; an additional
60-minute pending task. Explain how each affects counts, total time, and candidates.
The web chapter provides separate hints and collapsed reference answers.

Inputs are explicitly bounded: task dictionaries contain string titles and bool
done fields; estimates are absent, None, or integers, excluding bool; budget is a
nonnegative integer. This is not public-input validation, persistence, concurrency
control, or an API. The while example is not a production retry loop.

暂停时记录文件、输入、输出、已验证边界、未解决疑问、下次第一步。恢复时先运行
最后成功的版本，再预测一个输入变化。There is no fixed weekly schedule.

## Maintainer checks (not learner prerequisites)

The site reads these source files at build time. A JSON allowlist controls the
published ZIP; no tests, credentials, caches or environment files belong in it.
Run commands below from the repository root with installed tools:

```sh
python3 scripts/build-js2py-lab.py --lab u03-control-flow
python3 -m unittest discover -s scripts/tests -p test_js2py_control_flow.py -v
python3 scripts/test-js2py-control-flow.py
```

The integration check requires uv and a managed Python 3.13 interpreter. It runs
the actual downloaded files, expected failures and changed input from an empty
folder, with an intentionally incompatible parent project to verify isolation.
