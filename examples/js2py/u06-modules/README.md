# L06 — 模块与标准库 / Modules and the standard library / 模塊與標準庫

## 简体中文

前置 L00—L05；本实验只使用 CPython 3.13 标准库和本地模块，没有第三方依赖，不需要项目配置、文件读写或 pytest。2026-09-24 使用 3.13.15 验证。37 份 Python 文件是多文件实验组，不是每份都能直接执行：不要拆散文件，也不要把包内模块逐个当脚本启动。

解压后在 `u06-modules` 目录打开终端。先按正文逐组预测、运行、解释，再查看 `solutions/`。命令中的 `--no-project` 排除外层项目配置；保持普通本地搜索语义，不添加 `-I`、PYTHONPATH 或 sys.path 补丁。

```bash
uv run --no-project --python 3.13 python standard_library.py
uv run --no-project --python 3.13 python first_import/report.py
uv run --no-project --python 3.13 python first_import/import_styles.py
uv run --no-project --python 3.13 python first_import/import_twice.py
uv run --no-project --python 3.13 python bindings/observe.py
uv run --no-project --python 3.13 python entry_points/use_noisy.py
uv run --no-project --python 3.13 python entry_points/use_quiet.py
uv run --no-project --python 3.13 python entry_points/quiet_report.py
uv run --no-project --python 3.13 python locations/show_context.py
cd locations
uv run --no-project --python 3.13 python show_context.py
uv run --no-project --python 3.13 python -m show_context
cd ..
cd package_demo
uv run --no-project --python 3.13 python -m task_tools.app
uv run --no-project --python 3.13 python check_import.py
cd ..
uv run --no-project --python 3.13 python cycle_fixed/run.py
```

下面都是**预期失败**，不表示安装失败。每条从实验根目录单独执行；不要因一次命令失败就删除整个环境。

| 命令最后的 Python 参数 | 预期类别与原因 |
| --- | --- |
| `first_import/missing_name.py` | NameError：调用方没有绑定 task_rules |
| `first_import/missing_export.py` | ImportError：模块没有 remove_buffer |
| `missing_module.py` | ModuleNotFoundError：刻意不存在的名称 |
| `shadowing/show_source.py` | AttributeError：本地 statistics 遮蔽标准库；先打印实际路径 |
| `cycles/run.py` | ImportError：A 尚未定义函数，B 就要求取出该名称 |
| `-m task_tools.app` | ModuleNotFoundError：当前目录不包含该包 |

每行前加 `uv run --no-project --python 3.13 python`。另一个预期失败需先 `cd package_demo`，再运行 `uv run --no-project --python 3.13 python task_tools/app.py`：相对导入缺少父包上下文；正确形式为 `-m task_tools.app`，执行后 `cd ..` 回实验根目录。

同名遮蔽的修复只在副本里进行：将 `shadowing/statistics.py` 改名为 `practice_statistics.py`，重新启动进程检查实际来源与 `Average: 25`。`__pycache__`/`.pyc` 可以由普通导入生成；它们不保存跨进程的变量，不是源码，也不应加入提交或下载包。

```bash
uv run --no-project --python 3.13 python exercises/check_noisy.py
uv run --no-project --python 3.13 python solutions/check_fixed_entry.py
uv run --no-project --python 3.13 python solutions/fix_entry.py
cd solutions/independent
uv run --no-project --python 3.13 python check_import.py
uv run --no-project --python 3.13 python -m study_plan.app
cd ../..
```

练习先预测输出，再修复入口泄漏，最后从实验外的空目录独立建立 study_plan 包。验收每项阈值而非累积预算、零值/空输入、坏文本行号、未知错误传播、结果与输入隔离；分别验证导入探针和 `-m` 业务入口。完整机制、逐条输出、边界输入及暂停点见三语正文。本批不是文件持久化、依赖工程或 FastAPI 后端。

## English

Complete L00–L05 first. This is a standard-library-only CPython 3.13 multi-file lab (verified with 3.13.15 on 2026-09-24), not a project scaffold. Keep each group intact: 37 source files include helpers, so run the supported entry commands above rather than each file independently. Start in the extracted lab root except for explicit `cd` steps; do not add isolated mode or search-path workarounds.

The table lists intentional NameError, ImportError, ModuleNotFoundError and AttributeError cases. Directly running `task_tools/app.py` from `package_demo` is also an expected relative-import failure; `python -m task_tools.app` from that containing directory is the supported entry. In a copy, rename local `statistics.py` and use a fresh process to verify the shadowing repair. Bytecode caches may appear: they are not source files or cross-process application state.

Predict first, repair the leaking entry second, and build your own study_plan package from an empty directory outside this download third. Verify individual thresholds (not cumulative budget consumption), empty/zero/bad inputs, rejection row numbers, unknown-error propagation, input/result isolation and both import and entry behavior. The complete explanations, outputs and pause/resume points are in the English lesson. No pytest or dependency-configuration knowledge is required from the learner.

## 繁體中文

先完成 L00—L05。這是只依賴 CPython 3.13 標準庫與本地模塊的多檔案實驗，於 2026-09-24 使用 3.13.15 驗證，不是專案腳手架。37 份源碼含輔助模塊，不能逐份直接啟動；保持各組完整，依上方命令與明確的 cd 步驟執行，不加隔離模式或搜索路徑補丁。

表中是刻意安排的名稱、導入、模塊缺失與屬性錯誤。在 package_demo 直接執行 task_tools/app.py 也應失敗，正確入口是從該目錄以 -m task_tools.app 啟動。同名遮蔽只在副本中改名，並用新進程核對來源。普通導入可產生位元組碼快取，它不是源碼或跨進程狀態。

先預測，再修復入口洩漏，最後從下載實驗外的空目錄獨立建立 study_plan 包。驗收逐項閾值而非累積預算、空值/零/壞輸入、拒絕行號、未知故障傳播、輸入與結果隔離，以及導入和業務入口的差異。完整機制、輸出、暫停與恢復方式見繁體正文；不把 pytest、依賴工程或框架當作前置知識。

## Maintainer verification (not learner prerequisites)

From the repository root:

```bash
python3 scripts/build-js2py-lab.py --lab u06-modules --check
python3 scripts/test-js2py-modules.py
```

Tests run entry commands in fresh processes with controlled working directories and local import paths preserved. They verify outputs/errors, dependency direction, import safety with a failing-entry sentinel, independent-package behavior, empty-directory reconstruction and exact allowlisted ZIP bytes. Cache files are allowed only under expected `__pycache__` directories; source bytes and surrounding incompatible project files must not change. Maintainer tooling is not added to the learner download.
