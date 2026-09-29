# d02-sql — SQL、結果形狀與參數邊界

核驗日期：2026-09-28。獨立下載實驗，全部使用真實 PostgreSQL，不能用 SQLite 或瀏覽器 Python 替代。完整教材是 `module-22-sql` 的三語版本。

## 目標與前置

前置 L00–L14、H01–H06；D02 另需 D01，D03 另需 D02。D01 學習者不需提前會 SQL 或運維。先讀教材中的機制解釋再執行本文件；README 是可重建運行指南，不把安裝成功當掌握。

本實驗驗收 SQL、結果形狀與參數邊界。模型版本 `d01-d03-v1`；`model-contract.json` 給出字段與 ORM 銜接，`sql/schema.sql` 是可執行 DDL。身份/權限尚未實現：users 是測試人員，不是可登錄賬號。舊 H 字段明確演進：done 變 status（todo/doing/done），note 變 description（可空），minutes 保留為非負估時；新增用戶、項目、成員和時間字段。這不是對已有內存數據自動遷移。

## 固定環境，不安裝系統服務

- PostgreSQL 18.6（本機 Homebrew，服務端實際 `server_version_num=180006`）；官方發佈日期 2026-08-13。
- CPython 3.13.15，uv 0.12.13，pytest 8.4.2，psycopg[binary] 3.3.6。
- `requires-python = ">=3.13,<3.14"`；uv package=false；公共 PyPI 的真實 uv.lock。
- 僅 macOS/Homebrew 環境已實測；其他 OS 安裝、TCP/TLS 和生產配置未實測。無 Docker、ORM、認證、前端依賴。

工作目錄必須是解壓後的 `d02-sql`，不是上級目錄。此機器工具已有，**不要 brew services，不要連接默認 5432，不要初始化現有目錄**。

```bash
export PATH="$HOME/.local/bin:$PATH"
export UV_PYTHON_INSTALL_DIR=/tmp/langshift-js2py-python-20260928
export UV_CACHE_DIR=/tmp/langshift-js2py-uv-cache-20260928
export PG_BIN=/opt/homebrew/bin
"$PG_BIN/postgres" --version
"$PG_BIN/initdb" --version
"$PG_BIN/pg_ctl" --version
"$PG_BIN/psql" --version
uv --version
uv sync --locked
uv run --locked python --version
```

版本不匹配先停下。`PG_BIN` 是程序目錄；`psql` 是客戶端；`postgres` 是服務器；`initdb` 只創建新存儲；`pg_ctl` 按明確目錄啟動/停止進程。安裝物、運行進程、數據目錄不是一件事。

## 認領獨佔集群與數據庫

```bash
uv run --locked python labctl.py start
uv run --locked python labctl.py status
uv run --locked python labctl.py dsn
uv run --locked python labctl.py reset --yes-reset
```

start 的具體順序：新建短路徑 `/tmp/lsdb-*`（macOS 可顯示 /private/tmp）；目錄和 socket 均 0700；保存匹配的 `.lab-state.json` 與目錄 marker；initdb 新目錄；關閉 TCP；為私有 socket 選端口；pg_ctl 用顯式 -D 和 server.log 啟動；隨機管理角色建立 `langshift_lab` 數據庫和普通 `lab_student` 角色。數據庫是 cluster 內的邏輯命名空間，角色是數據庫身份，不是 users 表的用戶。Unix socket 是通信入口，DSN 是地址/選項，連接才是活動會話。

本地 trust 僅因目錄私有且 TCP 禁止才用於無密碼練習；同一 OS 用戶下的進程和 root 不在隔離範圍內，不能複製到公網或生產。連接、reset、stop 都驗證所有權；SQL 連接還驗證服務端數據目錄、系統標識和版本。腳本忽略 DATABASE_URL，不接受任意遠端 DSN；不要修改這些防護。

reset **有損重建自己數據庫的四表**，打印 `schema + seed ready: users=2 projects=3 members=4 tasks=5`。每次業務 pytest、D03 demo 也會 reset，因此不要並行啟動兩個運行器，不要拿這裡保存業務數據。停啟不會 reset；系統可能清理 /tmp，所以它仍不是長期保存或備份方案。

## PostgreSQL 環境邊界

`labctl.py` 自身在啟動或任何 SQL 連接前檢查環境，直接透過 Python 匯入呼叫也一樣：**拒絕除 `PG_BIN`、`PGHOST` 外的全部 `PG*` 變數**，包括空值和未知名稱。這也會保守拒絕雖已被顯式覆蓋的 `PGPORT`、`PGUSER`、`PGDATABASE`，不只 `PGHOSTADDR`、`PGSERVICE`、`PGSERVICEFILE`、`PGPASSFILE`、`PGPASSWORD`、`PGOPTIONS`。錯誤只列變數**名**，不列印值。啟動或執行 SQL 前，在實驗 shell 中 unset 報出的變數；不要把其他服務設定或憑證複製進實驗。

`PG_BIN` 仍用於選擇工具目錄。`PGHOST` 仍被接受但忽略，因為每條 DSN 都顯式指定自有私有 socket；維護 runner 的 `PGHOST=/nonexistent/...` 驗證仍成立。`DATABASE_URL` 仍忽略。所有子行程（包括 initdb、pg_ctl、psql）都使用清除全部 `PG*` 和 `DATABASE_URL` 的環境，工具和資料路徑顯式指定。Python 連接不暫時修改行程環境，因此 D03 並行連接不存在環境還原競態。

管理員和學生的每條 DSN 均顯式指定自有 root 下**內容為空、權限 0600 的 `empty.pgpass`**，不使用預設 `~/.pgpass`。新集群和已有自有集群均可建立該檔案；符號連結、非空、擁有者錯誤、非一般檔案或權限錯誤均拒絕。psql 同時使用 `-X -w`（不讀啟動檔案、不提示輸入密碼）。隨機管理員及伺服器資料目錄／系統識別碼／版本核驗保留，不改業務 SQL。

**錯誤的連接環境不阻止清理：** `status` 使用乾淨環境呼叫 pg_ctl；`stop` 在乾淨 Python 子行程中完成相同的伺服器身分核驗，再停止顯式指定的自有資料目錄。不會繞過 marker／PID／身分檢查失敗。停止後須清除報出的變數才能重新 start。匯出的 `dsn` 只是連接描述，不是沙箱：不要交給繼承其他連接預設值的任意客戶端；請使用 `labctl.py psql`。

`tests/test_environment.py` 新增 50 例：連接／啟動前 mock 拒絕、子行程環境、passfile、面對自有 loopback 監聽器的直接 CLI 拒絕、私有 socket 下 PGHOST／DATABASE_URL 相容，以及污染環境下 stop／status／重新啟動恢復。該模組覆蓋業務測試的自動 SQL reset fixture，避免負向測試在拒絕前先連接。這裡只驗證列出的路徑，不宣稱涵蓋所有攻擊；同一 OS 使用者／root 對行程或檔案的竄改不在隔離範圍內。

## 運行、解釋和驗收

```bash
uv run --locked python labctl.py psql --file sql/queries.sql
uv run --locked python demo.py
uv run --locked pytest -q
```

應有 **66 passed**（原 16 例業務測試 + 50 例環境測試），耗時不固定。故意錯誤 SQL 的 ERROR 是預期；普通命令失敗不能被忽略。D01：23505 重複、23503 壞外鍵、23514 CHECK、23502 NULL、22001 長度；本版本刪除引用的 RESTRICT 是 23001。D02：注入載荷作為原字符串保存，tasks 不被刪除；非法排序/分頁在 Python 拒絕。D03：後步 23503，後續查詢 25P02，rollback 後零殘留；真實兩連接的結果分別為讀提交 [30,40]、可重複讀 [30,30]、丟失更新 37、原子累加 42、唯一競爭一行、鎖超時 55P03、舊快照更新衝突 40001 後完整重試 42。

`demo.py` 的輸出以教材為準，D02 確定 ID 需要先 reset；D03 每個場景自己 reset。測試不是編譯：實際啟動的服務器執行了約束、參數和值轉換、事務與鎖。獨立題參考在 answers 中，先自己嘗試；不是主模型新增字段，也沒有自動接入 HTTP。

## 文件職責

- `labctl.py`：獨佔啟動、地址、身份驗證、reset、psql、stop；無全局服務操作。
- `sql/schema.sql` / `sql/seed.sql`：三章相同結構與確定種子；DDL 哈希在 model-contract。
- `sql/*.sql`：本章查詢或明確標記的失敗實驗。
- `tests/`、`conftest.py`：業務測試每例重置自己的數據庫；參考變式也執行驗證。
- `answers/`：獨立題參考，不要先抄。
- `pyproject.toml`、`uv.lock`、`.python-version`、`.env.example`：依賴與配置；env.example 僅文檔，不自動加載。
- `README.md`、`README.zh-cn.md`、`README.zh-tw.md`、`sources.json`、`model-contract.json`：復現、來源和銜接。
- `FILES.json`：包內文件 allowlist；倉庫同名 `../d02-sql-files.json` 用於主線打包。數據目錄、.lab-state.json、.venv、cache 和憑證不進入包。

## 安全停機與恢復

```bash
uv run --locked python labctl.py stop
uv run --locked python labctl.py status
uv run --locked python labctl.py start
uv run --locked python labctl.py stop
```

stop 先核對 marker/PID 目錄/健康服務器身份，然後對自己的 -D 執行 fast shutdown 並等待；status 返回 running=false、pg_ctl_status=3。fast 會斷開本集群連接並回滾未提交事務，保留提交數據與日誌；不對其他 postgres 發信號，不 brew services，也不刪目錄。停止後重新 start 是恢復同一存儲，不是 initdb。

若連接失敗先查 status 與所打印 root 的 server.log；若版本錯查 PG_BIN；若缺表確認是否準備數據；若 marker/服務器身份不符則拒絕重置與停止，必須查明原因，不能刪除 marker 或改成用戶數據庫來繞過。首次啟動中途失敗會嘗試只停止剛分配目錄，異常保留，後續先查 status 和日誌，不對舊目錄再 initdb。若健康檢查也無法完成，控制腳本寧可拒絕；不要用 killall 兜底。

暫停時保存目錄、root、最後成功命令、測試結果、失敗錯誤碼和下次第一步。/tmp 自動清理後應從全新解壓目錄開始；不要拿無 marker 的舊數據冒充新集群。

## 邊界與官方來源

正常停啟持久性不是災難恢復。本實驗沒做生產備份/恢復、斷電、提交時斷網、Serializable 全矩陣、真實死鎖、認證、權限、連接池或容量壓測。後續 ORM 應保留約束名稱/類型和失敗測試；updated_at 不自動更新；至少一個負責人和創建者的項目權限不是外鍵保證的。

下列官方來源核驗於 2026-09-28。psycopg 文檔站當次 403，讀取同官方倉庫 3.3.6 標籤的文檔源碼；PostgreSQL 文檔與 18.6 發佈頁可讀取。

- https://www.postgresql.org/docs/18/queries.html
- https://www.postgresql.org/docs/18/queries-table-expressions.html
- https://www.postgresql.org/docs/18/queries-limit.html
- https://www.postgresql.org/docs/18/functions-comparison.html
- https://github.com/psycopg/psycopg/blob/3.3.6/docs/basic/params.rst
- https://github.com/psycopg/psycopg/blob/3.3.6/docs/basic/usage.rst
- https://www.postgresql.org/docs/release/18.6/
