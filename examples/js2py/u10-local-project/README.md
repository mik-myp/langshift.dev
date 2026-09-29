# L10 — Independent reproducible local project / 独立可复现项目 / 獨立可重現專案

Verified baseline: 2026-09-28; CPython 3.13.15, uv 0.12.13, pytest 8.4.2.
The project uses the standard library at runtime. pytest is a development dependency.
Work from the extracted `u10-local-project` directory:

```sh
uv sync --locked
uv run --locked python check_import.py
uv run --locked python -m pytest -q
uv run --locked python -m task_app.app
uv run --locked python -m task_app.app
```

The root suite has 15 tests. Import prints only the module names and must not
create `_output`. First entry: `Source: new file`, `Changed: 1`, `Tasks: 3`,
`Pending minutes: 35`. Repeated entry: existing file and `Changed: 0`, same totals.
Business state lives only in `_output/tasks.json`, anchored to this project.

这是参考实现，先按正文契约在空目录独立实现，再展开答案。只在副本中试验损坏输入；
fixtures 不修改。损坏/错误形状/错误编码不得变成初始化成功，不得覆盖原字节。
关闭文件不是回滚；序列化前置不提供原子、并发或抗崩溃保证。本项目不是后端服务。

這是參考實作，先按正文契約在空目錄獨立完成，再展開答案。只在副本中試驗損壞輸入；
fixtures 不修改。損壞/錯誤形狀/錯誤編碼不得變成初始化成功，不得覆蓋原始位元組。
關閉檔案不是回滾；序列化前置不提供原子、並行或抗崩潰保證。本專案不是後端服務。

Tests create their own temporary directories with `TemporaryDirectory`, never a
real user's directory. Passing a path to `main(path)` is a testable function
boundary, not public arbitrary-path upload support. The ordinary entry uses its
owned fixed path. Do not run with Python -O. Do not copy environments or secrets.

## Independent follow-up / 独立变式 / 獨立變式

Add a stable-order greedy plan: unfinished items only; ordinary nonnegative int
budget; skip a too-large item but keep considering later items; exact fit and zero
are accepted; return fresh records and used minutes; do not mutate the source.
This is not a globally optimal knapsack algorithm. Answer and two tests are under
`solutions/`, excluded from the root suite until explicitly selected:

```sh
uv run --locked python -m pytest -q solutions/test_new_requirement.py
```

Before moving on, recover in a separate empty directory using source, declarations,
version file, lock and owned input fixtures; sync, import, test and run again.
The environment restore does not back up user data: test data recovery separately.

临时数据、.venv、pytest/字节码缓存不进下载。ZIP 与网页共享规范源码。
暫存資料、.venv、pytest/位元碼快取不進下載。ZIP 與網頁共用規範原始碼。
