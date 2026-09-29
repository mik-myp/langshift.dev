# H04 — Pydantic 輸入輸出邊界與內存 CRUD

[English](README.md) · [简体中文](README.zh-cn.md)

這是完整、獨立的本地 API，不是生產存儲。前置為 H03 同步服務與 L11/L12 註解和模型，不導入其他章節實現。API 自動測試與 fixture 在 H06 正式教學；本實驗讀者使用完全可見的 curl 做驗收。

## 復現環境

**2026-09-28** 在 macOS arm64 實測：CPython **3.13.15**、uv **0.12.13**、FastAPI **0.135.1**、Uvicorn **0.42.0**、Pydantic **2.12.5**。這是驗收版本，不是“最新”承諾。公開 PyPI 的 `uv.lock` 固定間接依賴，包括 Starlette 1.7.0、pydantic-core 2.41.5。`requires-python` 為 `>=3.13,<3.14`；`[tool.uv] package=false`。不需要前端依賴、數據庫、API key、httpx 或 pytest。

工作目錄為解壓的 `h04-validation`，或倉庫的 `examples/js2py/h04-validation`。以下應用、探針與答案命令均從此目錄運行。

```bash
uv --version
uv python install 3.13.15
uv sync --locked
uv run --locked python --version
```

維護者在 uv 命令前設置隔離位置：

```bash
export PATH="$HOME/.local/bin:$PATH"
export UV_PYTHON_INSTALL_DIR=/tmp/langshift-js2py-python-20260928
export UV_CACHE_DIR=/tmp/langshift-js2py-uv-cache-20260928
```

普通讀者可用 uv 默認位置；臨時目錄不是項目輸入。正常運行不重新生成鎖文件。維護者解析使用 `uv lock --default-index https://pypi.org/simple`，安裝與執行使用 `--locked`。

## 正文與路由契約

| 字段 | 創建 | PATCH |
| --- | --- | --- |
| title | 必填 str，1–120 字符，不能全為空白，保留原字形與兩側空白 | 遺漏保留，合法字符串替換，null 拒絕 |
| minutes | 必填嚴格非負 int，拒 bool、text、float | 遺漏保留，0 也應用，null 拒絕 |
| done | 嚴格 bool，默認 False | 遺漏保留，顯式 false 也應用，null 拒絕 |
| note | str 或 None，最多 1000 字符，默認 None，空串合法 | 遺漏保留，字符串替換，null 清空 |
| id | 服務生成進程內遞增正整數 | 客戶端字段拒絕 |
| internal_tag | 服務添加 `h04-memory-only` | 客戶端字段拒絕，永不公開 |

長度按 Python 字符串計算，不是字節數或視覺字形。未知字段包括 `id`、`user_id`、`internal_tag` 均為 422。拒絕自報身份不等於認證身份：這裡沒有用戶概念。

- `GET /health`：200，`{"status":"ok"}`。
- `POST /tasks`：201，完整公開任務；缺字段、畸形 JSON 或不合法正文為 422。
- `GET /tasks`：200，`{items, limit, offset, total}`，按 id 排序。`limit=20` 默認，範圍 1–100；`offset=0` 默認，非負；非法查詢為 422。超出末尾是空頁，不是 404。
- `GET /tasks/{task_id}`：200，公開任務；合法但不存在 id 為 404；非法 id 為 422。
- `PATCH /tasks/{task_id}`：200，完整更新後公開任務；`{}` 不修改。非法字段 422；合法正文但記錄不存在為 404。
- `DELETE /tasks/{task_id}`：204，**正文零字節**；不存在/重複刪除為 404。

沒有 PUT、認證、用戶隔離、項目關係、冪等鍵或最終 capstone 狀態枚舉。創建/讀取/更新和列表 items 中公開任務恰好包含 `id`、`title`、`minutes`、`done`、`note`。

## 請求前先理解模型流向

`models.py` 區分 `TaskCreate`、`TaskPatch`、`TaskStored`、`TaskPublic`。輸入嚴格驗證並拒絕未知鍵；title 檢查 `value.strip()` 但返回原 `value`。公開模型故意忽略白名單外字段，`TaskPage` 對列表內記錄執行同樣規則。

運行兩個講解探針：

```bash
uv run --locked python probe_models.py
uv run --locked python probe_patch.py
```

第一個對比寬鬆轉換 `"25"` 和嚴格拒絕 `True`、`"25"`、`25.0`，並拒絕負整數；證明沒有默認值的 `str | None` 仍必填。它們只是模型實驗，不是 HTTP 驗收。

`TaskPatch` 有合法佔位默認值：`title="Untitled"`、`minutes=0`、繼承的 `done=False`、`note=None`，從而支持省略非 nullable 字段。**只有 `model_dump(exclude_unset=True)` 可以合併到存儲。** 佔位值不是更新指令。顯式 false、0、等於默認值的 title、null 都必須保留。`exclude_none` 丟清空意圖，`exclude_defaults` 丟 false/0；探針同時打印正確合併與故意錯誤的 dump。

`app.py` 在臨時字典中合併，調用 `TaskStored.model_validate` 後才替換記錄。`model_copy(update=...)` 不會自動驗證更新。id/內部字段不來自請求；處理函數故意返回完整存儲字典，由 `response_model` 過濾實際 HTTP 輸出，避免把“沒有存內部鍵”誤當“確實完成過濾”。

## 啟動空服務，運行工作單

終端 A：

```bash
uv run --locked python -m uvicorn app:app --host 127.0.0.1 --port 8004 --workers 1
```

不啟用 reload，不暴露 `0.0.0.0`。`--workers 1` 顯式覆蓋外部默認設置，但不消除線程池併發。終端 B：

```bash
curl -sS -i http://127.0.0.1:8004/tasks
bash requests.sh
```

`requests.sh` 從空內存開始，發送 **25** 次可見請求。它打印而不自動斷言；必須閱讀響應，curl 默認退出碼即便收到 HTTP 錯誤也可能為零。`-i` 顯示狀態/頭，`-X` 選方法，`-H 'Content-Type: application/json'` 標明 JSON，`--data-binary` 發原正文。JSON 和含 `&` 的 URL 應加引號。

核對順序：

1. 空列表、兩個 201、第二頁 id=2/total=2，title 空白保留。
2. PATCH done 保留 note；`{}` 不變；false/0 應用；note 能替換與顯式 null 清空。
3. 八個錯誤正文全為 422，沒有新記錄。
4. 非法路徑/查詢 422；合法但不存在 id 為 404。
5. GET 與存儲一致；DELETE 正文零字節；讀取/重複刪除為 404；最後只留 id=2。任務響應都不包含 `internal_tag`。

第一次創建的實際正文：

```json
{"id":1,"title":"  Read HTTP  ","minutes":25,"done":false,"note":"keep me"}
```

`minutes=true` 為 422，`loc=["body","minutes"]`、`type="int_type"`；與合法但不存在 id 的 404 不同。錯誤可能回顯輸入，因此只用虛構數據，不能把默認錯誤格式當成生產脫敏政策。

自行補測缺 title/minutes、`done=1`、`note=1`、非 nullable 字段 null、自報 id/內部字段、畸形 JSON、長度邊界：120/1000 通過，121/1001 拒絕。可在本地文件準備長正文，用 `--data-binary @payload.json` 發送。被拒 PATCH 後 GET 不應發生部分修改。記錄狀態和字段，而不是隻寫“請求成功”。

## 破壞性重啟與恢復：僅可丟棄數據

工作單執行後 id=2 仍在，在終端 A Ctrl-C 退出**自己的**服務，再用同一命令重啟。GET `/tasks` 應 items 為空、total=0；GET `/tasks/2` 應為 404；新建 id 又為 1。這是實際數據丟失與 id 重用，沒有備份或數據庫能恢復舊內存。

恢復學習檢查點的方法是重啟為空，再重放工作單。不關閉別人的監聽者。端口衝突時停止自己的服務或換空閒端口並同步改 URL；導入錯誤時先核對工作目錄與 `app:app` 兩側，不要先重裝依賴。

## 獨立重建與變式

在新目錄只保留環境文件與契約，自寫模型/CRUD，解釋四類模型，通過請求驗收後再看答案。記錄一個問題的現象、所屬層、根因、修復和複驗。

再加 `/reports/remaining?max_minutes=20`：統計未完成且分鐘數不超過閾值的任務；默認 60，允許 0，拒負數。只返回 count/minutes，與分頁無關。創建 Zero/0/false、Short/15/false、Long/90/false、Finished/10/true；20 應得 `{"count":2,"minutes":15}`，0 應得 `{"count":1,"minutes":0}`，-1 應為 422。

先嚐試，再運行參考（先退出當前服務）：

```bash
uv run --locked python -m uvicorn solutions.remaining_app:app --host 127.0.0.1 --port 8004 --workers 1
```

它明確複用**本實驗**的 `app`、`tasks`，從空內存添加路由，不導入別章。用 POST 準備四條數據，並用 HTTP 驗證報告。暫停筆記保存目錄、入口、最後成功請求及正文、自己的端口/終端、是否已退出、未解決問題和下次命令，始終寫明重啟會清空內存。

## 文件、正向白名單與未驗證邊界

同級 **h04-validation-files.json** 明確列出允許顯示/下載的源碼和文檔；禁止遞歸打包 `.venv`、`__pycache__`、uv 緩存、`.env`/憑證、日誌、編輯器文件與個人數據。`.gitignore` 不替代打包 allowlist。共享 loader/ZIP 由集成者處理。SOURCES.md 提供官方依據，VERIFICATION.md 記錄實際案例。

同步函數在線程池運行；單工作進程不是鎖，讀改寫與分配 id 不是事務。兩個 PATCH 會有丟更新風險，多工作進程持有不同字典。本實驗不保證持久化、身份授權、冪等重試、併發負載、跨進程一致性、容量、瀏覽器 CORS、代理/TLS、生產脫敏或部署；語言階段輔助函數不提供這些保證。語法檢查和模型探針不替代真實 HTTP 驗收。
