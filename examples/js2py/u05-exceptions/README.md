# L05 — 异常与调试 / Exceptions and debugging / 異常與調試

## 中文

这是内存任务处理的独立语言实验，不是完整后端工程。先完成 L00—L04；无需导入、第三方包、pytest、文件读写或项目配置。

解压后在 `u05-exceptions` 目录执行正文命令；每个脚本完整独立，替换命令最后的文件名即可：

```bash
uv run --no-project --python 3.13 python errors/traceback_chain.py
uv run --no-project --python 3.13 python recover_value.py
uv run --no-project --python 3.13 python finally_paths.py
```

第一条有意失败；不是安装失败。22 份 Python 文件在普通模式下有 9 份预期异常：

| 文件 | 预期 |
| --- | --- |
| errors/traceback_chain.py | ValueError，原始 int 位于第 2 行；先打印 Starting report |
| errors/debug_observation.py | ValueError，第 4 行；先打印值与类型 |
| errors/unexpected_type.py | TypeError，第 3 行 |
| errors/negative_minutes.py | ValueError，第 6 行 |
| errors/narrow_try.py | ValueError，第 2 行；显示故障必须暴露 |
| errors/reraise.py | ValueError，原始第 3 行保留；先打印上下文 |
| errors/chained_error.py | ValueError，第 7 行；保留原始转换原因 |
| errors/finally_unhandled.py | TypeError，第 2 行；finally 先打印 |
| pitfalls/assert_validation.py | AssertionError，第 3 行；反例，不用于生产校验 |

`debug_logic.py`、宽 try、finally return、部分修改等反例可能正常退出；读输出不能只看退出码。

```bash
uv run --no-project --python 3.13 python -O pitfalls/assert_validation.py
uv run --no-project --python 3.13 python -O errors/negative_minutes.py
```

第一条错误地接受 -5，第二条仍应 ValueError。大写 O 是 Python 的优化选项，放在脚本前；用来验证 assert 会消失，不是让你常规启用。

先完成三层练习，再看 solutions。从空目录创建自己的 `import_report.py`，运行：

```bash
uv run --no-project --python 3.13 python import_report.py
```

核对空数据、全拒绝、零分钟、顺序和行号、缺字段/类型错误传播、同类内部故障传播、输入不变与重复结果隔离。完整解释、输出和验收在三语正文；未知异常不返回伪成功报告。示例只保证已声明的输入形状和解析边界，不提供通用回滚、文件导入、HTTP 错误处理或数据库事务。

## English

Complete L00–L04 first. Extract and run from `u05-exceptions`; each Python 3.13 file is independent with no third-party dependencies, imports, project config or testing-framework prerequisite. Use the commands above and replace the final filename. The first command intentionally fails.

There are 22 scripts, including nine expected runtime failures listed above. Several counterexamples instead exit successfully with wrong behavior. Under `-O`, the assertion-based validator wrongly accepts -5; explicit raise still rejects it. Do not use assert for production input validation.

Attempt the exercises before opening solutions. Rebuild `import_report.py` from an empty directory and verify all success/rejection/unknown-error paths, ordering and row numbers, source preservation and independent repeated results. This is in-memory list processing, not file import, an HTTP service, resource management or a transaction. Full explanations and outputs are in the corresponding lesson.

## 繁體中文

先完成 L00—L04。在解壓後的 `u05-exceptions` 目錄執行上方命令；各檔案獨立，使用 Python 3.13，無需第三方套件、專案設定、匯入或測試框架。第一條命令刻意失敗。

22 份程式中有 9 份預期執行期異常，見上表；其他反例可能正常結束但行為錯誤。`-O` 下斷言校驗錯誤地接受 -5，而明確的 raise 仍然拒絕。不要用 assert 校驗生產環境的不可信輸入。

先做練習再看 solutions；從空目錄建立自己的 `import_report.py`，驗收空資料、全拒絕、零分鐘、順序與行號、未知錯誤傳播、輸入不變和重複結果隔離。這只是記憶體列表處理，不是檔案匯入、HTTP 服務、資源管理或交易。完整機制、輸出和限制見繁體正文。

## Maintainer verification (not learner prerequisites)

From the repository root:

```bash
python3 scripts/build-js2py-lab.py --lab u05-exceptions --check
python3 scripts/test-js2py-exceptions.py
```

The integration requires uv and Python 3.13. It runs the actual extracted download, ordinary/optimized modes and an empty-folder variant, checks isolation from an incompatible parent project, then executes maintainer behavior tests. The explicit allowlist is the only publishing source; no tests, credentials or project environment are included in this download.
