# H03 — 第一個同步 FastAPI 服務

[English](README.md) · [简体中文](README.zh-cn.md)

這是獨立的本地只讀任務 API 實驗。前置為 H02 的 HTTP 與 L13 的裝飾器，不假定已有後端框架經驗，也不導入其他章節實現。網頁正文解釋機制，本 README 隨源碼保存可運行契約。

## 環境與工作目錄

**2026-09-28** 在 macOS arm64 實測：CPython **3.13.15**、uv **0.12.13**、FastAPI **0.135.1**、Uvicorn **0.42.0**、Pydantic **2.12.5**。這是固定驗收版本，不是“最新”承諾。`uv.lock` 來自公開 PyPI，固定間接依賴，包括 Starlette 1.7.0、pydantic-core 2.41.5。`requires-python` 為 `>=3.13,<3.14`；`[tool.uv] package=false` 表示運行本地文件，不構建安裝當前項目。無需前端依賴、API key、數據庫、pytest 或 httpx。

進入解壓的 `h03-first-fastapi`；倉庫內則進入 `examples/js2py/h03-first-fastapi`。下面命令均在此目錄執行。

```bash
uv --version
uv python install 3.13.15
uv sync --locked
uv run --locked python --version
```

維護者隔離復現時，在執行 uv 前導出：

```bash
export PATH="$HOME/.local/bin:$PATH"
export UV_PYTHON_INSTALL_DIR=/tmp/langshift-js2py-python-20260928
export UV_CACHE_DIR=/tmp/langshift-js2py-uv-cache-20260928
```

這些 `/tmp` 目錄是可丟棄基礎設施，不屬於交付項目；普通讀者可以使用 uv 默認位置。為了運行實驗不要重新生成鎖文件。維護者使用 `uv lock --default-index https://pypi.org/simple` 解析，安裝和執行使用 `--locked`。

## 啟動、請求、退出

終端 A：

```bash
uv run --locked python -m uvicorn app:app --host 127.0.0.1 --port 8003 --workers 1
```

`app:app` 從此目錄導入模塊 `app`，取得其中的 `app` 對象。導入登記路由，Uvicorn 才打開監聽。`python app.py` 只執行定義隨後退出。顯式 `--workers 1` 避免繼承外部工作進程設置，但不表示同步處理函數串行運行。本次不要使用 reload；更不要把無認證服務綁定到 `0.0.0.0`。

終端 B：

```bash
curl -sS -i http://127.0.0.1:8003/health
curl -sS -i http://127.0.0.1:8003/tasks/1
curl -sS -i 'http://127.0.0.1:8003/tasks?limit=1&offset=1'
bash requests.sh
```

`-sS` 隱藏進度但顯示連接錯誤；`-i` 顯示狀態和頭；查詢 URL 的 `&` 要用引號保護。工作單有 **11** 個可見請求，打印證據但不自動判定通過。curl 默認進程退出碼並不保證 HTTP 成功。API 自動測試與 fixture 到 H06 才正式教學。

單項請求預期：

```http
HTTP/1.1 200 OK
content-type: application/json

{"id":1,"title":"Read HTTP","minutes":25,"done":false,"note":null}
```

以上省略動態響應頭。第二頁只包含 id=2，`limit=1`、`offset=1`、`total=2`。退出時在終端 A 按 Ctrl-C，只關閉自己啟動的前臺服務；再請求會連接失敗，而不是收到 404。

## 接口契約

- `GET /health`：200，`{"status":"ok"}`。這是進程存活，不是數據庫就緒。
- `GET /tasks`：200，`{items, limit, offset, total}`，按 id 升序。limit 默認 20，範圍 1–100；offset 默認 0，非負。超出末尾是空頁 200；`total` 是全部記錄數。
- `GET /tasks/{task_id}`：解析後的正整數，id 1/2 返回 200；合法但不存在返回 404 和 `{"detail":"Task not found"}`；文本或非正數為 422。
- 沒有寫操作。`POST /tasks` 為 405；未知路由為 404、`Not Found`。
- 公開字段 `id`、`title`、`minutes`、`done`、`note`，銜接 H04，但本章不教請求體模型。
- `/docs` 與 `/openapi.json` 暴露生成契約，能打開文檔不等於行為驗收通過。

## 故意失敗與恢復

1. 保持自己的服務運行，在另一個終端重複啟動。第二個進程非零退出，報 `address already in use`；原服務仍響應 `/health`。不要殺別人的監聽進程；停止自己啟動的服務，或換空閒端口並同步修改客戶端 URL。
2. 退出自己的服務，在實驗父目錄執行：

   ```bash
   uv run --project h03-first-fastapi --locked python -m uvicorn app:app --host 127.0.0.1 --port 8003 --workers 1
   ```

   預期 `Could not import module "app"`。找到項目環境沒有改變工作目錄。恢復為進入實驗目錄，或在父目錄加 `--app-dir h03-first-fastapi`。改成 `app:missing` 則報 `Attribute "missing" not found`，需要分別核對冒號兩側。
3. 在實驗根目錄啟動明確的錯誤應用：

   ```bash
   uv run --locked python -m uvicorn errors.broken_app:app --host 127.0.0.1 --port 8003 --workers 1
   ```

   終端 B 執行 `curl -sS -i http://127.0.0.1:8003/broken`。應為 500，正文 `Internal Server Error`，服務端回溯含 `RuntimeError: deliberate failure for H03`。退出它，重新啟動 `app:app`，複驗 `/health` 與 `/tasks/1` 均為 200。啟動失敗、輸入 422、缺失 404、程序 500 屬於不同層。

## 獨立任務與恢復筆記

只帶環境文件和上述契約，在新目錄重建服務，解釋導入、註冊、驗證、處理、JSON 序列化。再加 `/summary`，統計未完成任務 count/minutes，應得 `{"count":1,"minutes":25}`。先嚐試，後看獨立參考；參考自帶種子與路由：

```bash
uv run --locked python -m uvicorn solutions.rebuild:app --host 127.0.0.1 --port 8003 --workers 1
```

筆記保存工作目錄、應用入口、最後成功命令、請求/狀態/正文、端口及所屬終端、未解決問題、下次命令，並記錄服務是否已停。這裡的只讀種子在導入時重建，不是保存過的用戶數據。

## 文件、打包與邊界

- `app.py`：完整服務；`requests.sh`：可讀 HTTP 工作單。
- `errors/broken_app.py`：故意 500；`solutions/rebuild.py`：獨立答案。
- `.python-version`、`pyproject.toml`、`uv.lock`：可復現環境。
- `README*.md`、`SOURCES.md`、`VERIFICATION.md`：操作說明、官方依據、實際證據。

同級 **h03-first-fastapi-files.json 是明確正向 allowlist**，頁面和下載只使用列出的文件。禁止遞歸壓縮目錄：排除 `.venv`、`__pycache__`、緩存、`.env`/憑證、日誌、編輯器文件和個人數據。`.gitignore` 只是補充，不替代下載白名單。共享 loader/ZIP 由集成者統一接入。

驗收僅覆蓋本地、單工作進程、順序請求、固定只讀數據；不提供併發、身份權限、生產部署、瀏覽器 CORS、代理/TLS、性能、跨平臺保證。Python 語法通過不是 API 驗收。實跑 case 見 **VERIFICATION.md**，2026-09-28 核驗的官方來源見 **SOURCES.md**。
