# L07 — 文件、JSON 与资源使用 / Files, JSON and resource use / 文件、JSON 與資源使用

## 简体中文

前置 L00—L06。本实验使用 CPython 3.13 标准库，2026-09-24 用 3.13.15 验证，不需要第三方依赖、测试框架、类、数据库或服务端。下载包含 31 份 Python 源码、六份输入和本说明。保留所有目录；包内辅助模块不是独立入口。

**写入边界：** 仅在本下载副本或自己的练习目录运行。fixtures 为只读教学输入，包括故意损坏的文件；不要在原位修复。所有生成或破坏性演示只使用明确的 `_output/` 目录，里面不能放重要文件。不要把示例目标改成自己的真实文档。with 负责关闭文件，不会回滚截断或失败写入。

从解压的 `u07-files` 根目录执行，除非下方明确 cd。每个普通示例不依赖前一个脚本留下的内存。除了明确的首次/重复运行实验，其余示例会重置自己的实验输出。

```bash
uv run --no-project --python 3.13 python paths.py
uv run --no-project --python 3.13 python read_text.py
uv run --no-project --python 3.13 python read_cursor.py
uv run --no-project --python 3.13 python read_lines.py
uv run --no-project --python 3.13 python encoding_bytes.py
uv run --no-project --python 3.13 python read_binary.py
cd fixtures
uv run --no-project --python 3.13 python ../paths.py
uv run --no-project --python 3.13 python ../read_text.py
cd ..
uv run --no-project --python 3.13 python write_text.py
uv run --no-project --python 3.13 python write_modes.py
uv run --no-project --python 3.13 python cleanup_paths.py
uv run --no-project --python 3.13 python pitfall_truncate.py
uv run --no-project --python 3.13 python json_values.py
uv run --no-project --python 3.13 python json_limits.py
uv run --no-project --python 3.13 python json_file.py
uv run --no-project --python 3.13 python serialize_before_open.py
uv run --no-project --python 3.13 python validate_data.py
uv run --no-project --python 3.13 python inspect_documents.py
```

从新的解压副本连续运行两次，第二次刻意失败，第一次写入的字节不变：

```bash
uv run --no-project --python 3.13 python create_once.py
uv run --no-project --python 3.13 python create_once.py
```

不要为了隐藏第二次的 FileExistsError 就改成 w。使用过的输出会改变下次实验前提，暂停时要记录。

其他**预期失败**如下；在根目录给每个参数前加 `uv run --no-project --python 3.13 python`：

| 最后的参数 | 预期 |
| --- | --- |
| closed_stream.py | ValueError：读取已经关闭的流；之前读出的字符串仍然存在 |
| error_wrong_encoding.py | UnicodeDecodeError：ASCII 解码失败；已取得的流仍关闭 |
| error_missing_file.py | FileNotFoundError：已知缺失输入，块体不进入 |
| error_missing_parent.py | FileNotFoundError：w 不会创建缺失父目录 |
| error_directory.py | macOS 实测 IsADirectoryError；其他平台可能 PermissionError |
| pitfall_two_documents.py | JSONDecodeError：两个相邻对象不是一份 JSON 文档 |

`pitfall_truncate.py`、`json_limits.py` 和错误练习可能正常退出却暴露错误行为。不能用退出码代替契约核对。JSON 转义不等于文件编码；默认解码可接受非标准 NaN、重复键保留后值。独立任务校验拒绝非整数分钟，但不检测原文重复键，不提供通用严格解析或超大输入限制。

先预测，再修复恢复政策，最后从下载外的空目录重建 task_store。答案运行方式：

```bash
uv run --no-project --python 3.13 python exercises/unsafe_load.py
uv run --no-project --python 3.13 python solutions/recover_missing_only.py
cd solutions/independent
uv run --no-project --python 3.13 python check_import.py
uv run --no-project --python 3.13 python -m task_store.app
uv run --no-project --python 3.13 python -m task_store.app
cd ../..
uv run --no-project --python 3.13 python solutions/independent/run_store.py
```

错误练习写 `exercises/_output/repair.json`，修复示范写 `solutions/_output/repair.json`，独立参考写 `solutions/independent/_output/tasks.json`。其余写入位于实验根目录的 `_output/`。导入探针不得创建数据目录。已有合法空数组不应被重置成初始数据；已有损坏数据必须拒绝且字节不变。不要直接执行包内 app.py，应使用 -m 或外层薄入口。

完整解释、逐条输出、输入变式、两个暂停点与验收在三语正文。保存先校验与序列化，再打开 w，只保护相应的准备阶段失败；真正写入失败仍可能留下空/部分文件，不提供原子性、并发、断电持久性或备份保证。维护用故障注入和测试工具不是读者前置知识。

## English

Complete L00–L06 first. This is a standard-library-only CPython 3.13 lab, verified with 3.13.15 on 2026-09-24: 31 Python files, six fixtures and this README. Keep groups intact and run the commands above from the extracted root except for explicit cd steps. Package helper files are not standalone entries.

Treat fixtures as immutable known inputs; some intentionally contain malformed JSON or invalid UTF-8. All writes are limited to named `_output/` directories in this disposable lab copy. Never put valuable data there or substitute real document paths. Some scripts deliberately truncate their own scratch file. With closes acquired streams; it does not undo writes or restore old bytes.

The two create_once commands require a fresh copy with no once.txt: the first creates it, the second intentionally raises FileExistsError and preserves it. The failure table lists closed-stream, decode, missing-path, directory-as-file and concatenated-JSON failures. IsADirectoryError was verified on macOS; another platform may report PermissionError. Successful exit from a counterexample is not successful behavior.

Attempt prediction, repair and independent reconstruction before reading solutions. The repair only treats FileNotFoundError as an initial empty list. The full task store validates exact title/minutes/done records, rejects corrupted existing data without rewriting, distinguishes a missing file from a valid empty array, and never performs I/O on import. Run its module entry twice to observe persistence; the external run_store wrapper verifies the anchored location from a different cwd. Each exercise has its own output directory as listed above.

The default JSON decoder's NaN and last-duplicate-key behavior are explicitly taught. Task validation rejects noninteger minutes but does not detect original duplicate names or implement arbitrary upload limits. Validation/serialization before w preserves an old target for those preparation failures only. A write/close failure or crash may still damage the file; this is not atomic, concurrent or crash-safe production persistence. Full explanations, expected outputs and pause/resume records are in the English lesson.

## 繁體中文

先完成 L00—L06。本實驗僅使用 CPython 3.13 標準庫，於 2026-09-24 使用 3.13.15 驗證，包含 31 份 Python 源碼、六份輸入與本說明。保持目錄結構，依上方命令和明確的 cd 步驟執行；包內輔助模塊不是獨立入口。

fixtures 是不可原位修改的教學輸入，刻意包含損壞 JSON 與無效 UTF-8。所有寫入只發生在本副本內明確的 `_output/` 目錄，不可放重要資料，也不可換成真實文檔路徑。有些反例刻意截斷自己的實驗文件；with 會關閉已取得的流，但不撤銷寫入或恢復舊字節。

create_once 的兩條命令需從尚無 once.txt 的新副本開始，第二次預期 FileExistsError 且原文件不變。表中列出關閉流、錯誤解碼、路徑缺失、目錄當文件與串接 JSON 的預期失敗；目錄例在 macOS 驗證為 IsADirectoryError，其他平台可能 PermissionError。反例正常退出不等於行為正確。

先預測，再修復恢復政策，最後從下載外的空目錄獨立建立 task_store。只把 FileNotFoundError 當成初始化，損壞文件不得變成空資料或被覆蓋；合法空陣列也不得恢復初始任務。導入不進行 I/O；連續兩次模塊啟動驗證持久化，外層 run_store 入口驗證不同 cwd 下仍使用相同資料位置。各組只寫自己的輸出目錄。

正文明確解釋預設 JSON 解碼器的 NaN 與重複鍵後值行為；任務校驗拒絕非整數分鐘，但不檢測原文重複名稱或提供任意上傳限制。先校驗和序列化再開 w，只能保護準備階段失敗；寫出、關閉或崩潰仍可能損壞資料，不提供原子性、並發或斷電保證。完整機制、預期輸出、變式與暫停/恢復記錄見繁體正文。

## Maintainer verification (not learner prerequisites)

From the repository root:

```bash
python3 scripts/build-js2py-lab.py --lab u07-files --check
python3 scripts/test-js2py-files.py
```

Checks run normal Python import semantics in fresh processes and temporary directories. They verify generated bytes and allowed write locations, preserve every fixture/source and incompatible parent configuration, exercise first/repeated creation and persistence, inject failures to inspect closing and propagation, and reconstruct the independent package outside the download. Bytecode caches may be generated; caches, outputs, credentials, virtual environments and maintainer tooling are excluded from the download allowlist.
