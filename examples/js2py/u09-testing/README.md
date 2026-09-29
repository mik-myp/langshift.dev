# L09 — Basic automated testing / 基础自动化测试 / 基礎自動化測試

Verified 2026-09-28: CPython 3.13.15, uv 0.12.13, pytest 8.4.2.
Extract the full directory and work from `u09-testing`:

```sh
uv sync --locked
uv run --locked python first_check.py
uv run --locked python -m pytest -q
uv run --locked python -m pytest --collect-only -q
```

The normal suite collects SIX tests in `tests/`; all six pass.
The printed-check script says `Observed: 20` and `Checked`.
Durations and absolute paths vary. Use Python without -O.

在实验根目录执行。pytest 是 dev 依赖，不是业务运行依赖。默认发现只进入 tests；
errors、exercises 是明确指定才运行的教学失败。不要把未收集到测试当成通过。
在實驗根目錄執行。pytest 是 dev 依賴，不是業務執行依賴。預設發現只進入 tests；
errors、exercises 是明確指定才執行的教學失敗。不要把未收集到測試當成通過。

## Deliberate outcomes / 刻意结果 / 刻意結果

- `uv run --locked python wrong_check.py`: AssertionError, nonzero exit.
- `uv run --locked python -m pytest -q errors/test_wrong_expectation.py`: one failure, exit 1.
- `uv run --locked python -m pytest -q errors/test_false_green.py`: one pass, but no business call; deliberately worthless evidence.
- `uv run --locked python -m pytest -q errors/not_discovered`: no tests, exit 5.
- `uv run --locked python -m pytest -q errors/test_import_failure.py`: collection error, exit 2.
- `uv run --locked python -m pytest -q exercises/test_broken_study.py`: two failing cases, exit 1.

Repair the broken function in a DISPOSABLE copy; rerun the unchanged tests.
Then add tests for missing/wrong fields and illegal input; two greens alone do not
prove full contract validation. Do not alter expectations to agree with a bug.

## Independent answer / 独立答案 / 獨立答案

In `solutions/budget`, synchronize and run `uv run --locked python -m pytest -q`.
Nine plain-function tests cover normal, empty, exact, over-budget, zero, invalid,
and repeated calls with input preservation. No decorator, fixture parameter or
custom class is needed. Rebuild outside the download from requirements first.

临时缓存与 .venv 不进 ZIP，测试不能访问真实用户数据。源码和锁文件是恢复输入。
暫存快取與 .venv 不進 ZIP，測試不能存取真實使用者資料。原始碼與鎖定檔是恢復輸入。
