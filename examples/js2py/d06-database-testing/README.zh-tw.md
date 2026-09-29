# D06：隔離 PostgreSQL 測試與查詢計劃

本地多文件實驗，不能在 Pyodide 運行。當前目錄就是完整 canonical 源碼，不導入相鄰實驗。
網頁與下載使用顯式 `d06-database-testing-files.json` allowlist，不能把整個工作目錄遞歸打包。

## 1. 第一次運行前，分清解釋器、驅動與服務

先在終端進入解壓後的 `d06-database-testing` 目錄。CPython 執行 Python；uv 把鎖定依賴裝入 `.venv`，
但它們不會安裝或啟動 PostgreSQL 服務。`postgres` 是數據庫服務進程，`initdb` 初始化
一個新集群，`pg_ctl` 管理指定集群，`psql` 是命令行客戶端。四個二進制應來自同一套 18 版本安裝。
`psycopg[binary]` 自帶客戶端庫，並不包含數據庫服務器。

實測機器為 macOS arm64，Python 3.13.15、uv 0.12.13、PostgreSQL 18.6，二進制位於
`/opt/homebrew/bin`。若缺少工具，先依 SOURCES.md 的官方安裝頁面安裝 uv 與 PostgreSQL 18
二進制；不要初始化已有目錄，不啟動系統服務。其他 POSIX 系統把 PG_BIN 改成這四個程序
所在目錄的絕對路徑；下面的 Homebrew 路徑不是所有系統通用。不要用 root 運行。
本實驗依賴 Unix socket，未驗證 Windows。無需 Docker、`brew services`、雲賬號或密碼。

## 2. 安裝鎖定依賴並運行

下面兩個臨時 uv 目錄隔離這臺共享機器上的解釋器/緩存，不是數據庫數據目錄。
`uv sync --locked` 不應偷偷改鎖；鎖從 public PyPI 真正生成。Python 範圍為
`>=3.13,<3.14`，`[tool.uv] package=false`。

```bash
export PATH="$HOME/.local/bin:$PATH"
export UV_PYTHON_INSTALL_DIR=/tmp/langshift-js2py-python-20260928
export UV_CACHE_DIR=/tmp/langshift-js2py-uv-cache-20260928
export PG_BIN=/opt/homebrew/bin
uv --version
"$PG_BIN/postgres" --version
uv python install 3.13.15
uv sync --locked
uv run --locked python pg_sandbox.py --evidence /tmp/d06-database-testing-cleanup.json -- python -m pytest -q
uv run --locked python pg_sandbox.py -- python query_plan.py
uv run --locked python pg_sandbox.py -- python commit_failure.py
```

預期 **26 passed**，耗時和臨時路徑會變化。SQLAlchemy 2.0.54 是有意選擇的 2.0
維護線，不把它說成當前功能主線：2026-09-28 已有 2.1.1。固定 Alembic 1.20.0、
psycopg/psycopg-binary 3.3.6、FastAPI 0.135.1、Uvicorn 0.42.0、Pydantic 2.12.5, HTTPX 0.28.1、pytest 8.4.2；
間接依賴見 `uv.lock`。Web 版本與 H03–H06 統一，不在 ORM 章節無聲升級框架。Starlette 0.52.1 與 AnyIO 4.12.1 也對齊 H05/H06 的實測鎖。

## 3. 服務到底在哪裡，誰負責關掉

`pg_sandbox.py` 在 `/tmp/ls-pg-*` 用 mkdtemp 建立獨佔集群。集群是一份 PostgreSQL
服務數據目錄，裡面可有多個數據庫；測試數據庫是該集群內隔離的一份對象集合。
服務只監聽私有 Unix socket，目錄和 socket 權限為 0700，不開放 TCP。
本地 trust 僅適用於這份同一系統用戶掌控的短命實驗，不是生產安全方案。
marker/token 防誤接庫，不防同一 OS 用戶下惡意進程。

腳本依次 initdb、對獨佔目錄 pg_ctl start、創建非超級用戶 lab_owner（有 CREATEDB，
供 fixture 建庫）、創建隨機 js2py_lab_* 數據庫。繼承的 PG 設置、開發/測試 URL 會被移除。
只有子命令得到 LAB_DATABASE_URL 和所有權標記。safety.py 會拒絕普通開發/生產連接，
不是換個環境變量名便允許危險操作。每個測試另建數據庫，歸還連接、dispose 連接池，
再刪除自己那一庫；不使用 DROP FORCE 掩蓋連接洩漏。

finally 用 fast shutdown 停自己的服務，檢查 pg_ctl status 返回 3（未運行），再刪自己的
目錄。清理 JSON 中應有 server_version=180006、stopped=true、removed=true、status_after_stop=3。
子命令失敗也會清理；停止失敗則保留目錄與日誌並報錯，不能隨手殺所有 postgres 進程。
SIGKILL/斷電無法執行 Python finally；這時只能檢查輸出中的精確獨佔目錄與進程再人工恢復。

每次 wrapper 調用都是新集群。若需要連續執行多條命令，使用
`uv run --locked python pg_sandbox.py -- bash`，在這個子 shell 內操作，最後 `exit`。
普通 shell 不會永久得到數據庫配置。實驗臨時性不代表生產服務應該丟棄數據。

## 4. 先定位，再恢復

| 觀察 | 檢查與處理 |
| --- | --- |
| 找不到 PostgreSQL / 主版本錯誤 | 檢查四個程序和 PG_BIN，不改接現有服務。 |
| Refusing database access | 使用 wrapper；不要刪除保護條件，也不要改接開發庫。 |
| relation does not exist | D04 在同一個 sandbox bootstrap；D05/D06 對這一庫 upgrade，不是對上次已經刪除的庫。 |
| PendingRollbackError / Session 已失敗 | 結束失敗工作單元，rollback 或丟棄 Session；不能只重試最後一條 INSERT。 |
| pool timeout / 數據庫仍有連接 | 關閉所有 Session/Connection，再 dispose；擴大池會掩蓋洩漏。 |
| 遷移拒絕舊數據 | 檢查 revision 和異常行，按明確業務規則修正後重跑，不用 stamp 跳過失敗。 |
| stopped=false | 保留證據/server.log；只停輸出中自己的集群，停止確認前不刪目錄。 |

## 5. 模型銜接與邊界

四表和原約束名與 D01–D03 一致。H 的 done=false/true 映射 todo/done，doing 為新增狀態；
note 改為可空 description，minutes 保留估算；數據庫 bigint identity 替代內存 ID 分配，
沒有偷偷導入舊 ID。顯式加入 Project/User/ProjectMember 和任務外鍵。
updated_at 不會自動更新，SQL btrim 也不等於 Python 的全部 Unicode 空白規則。
所有外鍵為 RESTRICT。D05 經可空擴展、回填、默認值/NOT NULL/CHECK 增加 priority。
D06 保持該 head，複合索引是獨立測試庫內實驗，不是隱藏的下游結構變更。

這裡不是已完成鑑權的多用戶服務。後續 S 章節必須遷移密碼哈希、啟用狀態、auth_version，
從驗證後的身份推導創建者，並實施成員與負責人規則；外鍵存在不等於有權限。
沒有驗證生產性能、零停機遷移、網絡分區恢復、備份和授權。先做正文任務，再看 solutions。

## 6. 暫停與恢復記錄

記錄代碼差異、當前章節/revision、最後成功命令、已通過測試、未解決問題、下次第一步。
wrapper 退出後臨時集群不保留：保存生成數據的命令，不復制數據庫目錄。
`.venv`、`.pytest_cache`、`__pycache__`、`.env`、DB data、日誌、真實秘密都不能進入下載包。
官方資料核驗與實際執行基線：**2026-09-28**，詳見 SOURCES.md。
