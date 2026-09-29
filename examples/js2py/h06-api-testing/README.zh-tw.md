# h06-api-testing：完整本地實驗

先閱讀對應 H05/H06 正文。本目錄獨立運行，不導入 H04 或旁邊實驗。
Python、HTML、測試源文件是唯一真源；網頁 loader 與下載包使用旁邊的
`-files.json` 明確清單，不從整個目錄遞歸收集文件。

## 環境與第一次運行

2026-09-28 實測：CPython 3.13.15、uv 0.12.13、FastAPI 0.135.1、
Uvicorn 0.42.0、Pydantic 2.12.5、Starlette 0.52.1、pytest 8.4.2。
HTTPX 0.28.1 是 TestClient 和真實客戶端使用的開發依賴。
要求 Python >=3.13,<3.14；這是應用，因此 uv package=false。
終端進入當前解壓目錄。鎖來自 public PyPI；不要用未經複核的升級替代鎖定同步。

```bash
uv sync --locked
uv run --locked python -m pytest -q
TASKS_APP_NAME="Learning tasks" uv run --locked python -m uvicorn task_api.main:create_app --factory --host 127.0.0.1 --port 8006
```

服務會持續運行。另開終端，**仍進入本目錄**：

```bash
uv run --locked python live_client.py --port 8006
```

真實客戶端要求空的、可丟棄的教學服務，創建測試數據並在 finally 刪除。
它檢查真實網絡、嚴格拒絕、PATCH 三態、分頁、輸出過濾及 204/404 清理。
用 Ctrl-C 停服務。清理後可以重跑客戶端，但 ID 不必回到 1；只有重啟進程才
重建內存數據和編號。不要對已有業務數據執行這個驗收。

urllib 客戶端逐個嘗試自有 ID；某次 DELETE 或讀回檢查失敗會記錄下來，
不會跳過後續 ID。結束輸出 CLEANUP FAILED 和清理未確認的 ID，重跑前只檢查
這些記錄。清理失敗使程序非零退出；若主體也失敗，保留原 traceback 並單獨
報告清理診斷，不把任何一種失敗偽裝成功。不刪除其他記錄，也不承諾服務不可用
時仍可刪淨。

## 職責與配置

`task_api/main.py` 組裝應用，每個 app 擁有自己的 store；`config.py` 讀取和
校驗環境字符串；`models.py` 負責輸入輸出；`store.py` 修改內存而不處理 HTTP；
`routes.py` 將 HTTP 映射為操作；`dependencies.py` 供應 store/settings/page，
並管理每請求一個臨時跟蹤文件。沒有隱藏異步 lifespan、數據庫、登錄或權限。

TASKS_APP_NAME 是必填非空白的公開顯示文本，**不是秘密**。
TASKS_MAX_PAGE_SIZE 默認 100，接受 20..100 的 ASCII 十進制整數；下界保證
默認分頁 20 始終合法。配置在每次調用工廠時讀取一次，不在每請求讀取。
不會自動加載 `.env`。修改運行配置需要停止並以新環境重啟。
直接構造 Settings 是可信內部測試輸入，不是外部配置校驗接口。

```bash
env -u TASKS_APP_NAME uv run --locked python -m uvicorn task_api.main:create_app --factory --host 127.0.0.1 --port 8006
TASKS_APP_NAME="Learning tasks" TASKS_MAX_PAGE_SIZE=bad uv run --locked python -m uvicorn task_api.main:create_app --factory --host 127.0.0.1 --port 8006
```

這兩條是**預期啟動失敗**，不是 API 驗收通過。末行診斷指出 TASKS_APP_NAME
或 TASKS_MAX_PAGE_SIZE，但不回顯原值。修好變量，重放第一條成功啟動命令。
端口占用時停止自己的舊服務或換端口，不殺不明進程。導入錯誤先查工作目錄與
`task_api` 文件是否完整，改 CORS 不能修復導入錯誤。

## 契約與侷限

POST /tasks 返回 201；列表和 GET/PATCH /tasks/{id} 返回 200；DELETE 返回
204 空正文。不存在的正整數 ID 返回 404，非法輸入返回 422。ID 由服務器分配。
標題 1..120 字符、拒絕全空白、保留原字形和空格；minutes 是普通非負 JSON
整數，拒絕 bool/str/float；done 是嚴格 bool，默認 false；note 是可空文本，
最多 1000 字符，默認 null。PATCH 區分遺漏/賦值/null，只有 note 可以 null。
拒絕多餘請求字段；輸出不含 internal_tag。列表返回 items/limit/offset/total，
按 ID 排序；offset 數的是記錄而不是 ID。limit 為 1..100 並遵守配置上限。

TRACE acquire/use/release 對應真實 TemporaryFile 句柄，不是持久審計日誌或
數據庫事務。顯式 function scope 在正常響應發送前釋放；關閉資源不回滾修改。
不承諾生產併發、持久化、用戶隔離、部署、網絡安全、身份驗證或授權。
只監聽 127.0.0.1；實驗沒有真實用戶數據和憑證。

note 的遺漏/賦值/null 三態都要求 PATCH 與隨後 GET 為 200，完整內容均與
預期記錄相等。獨立空 PATCH 題從 done=true、非零 minutes、有 note 的記錄
開始，要求兩次完整響應都等於原記錄。只看 PATCH 響應未變，不能證明存儲未變。

## H06 測試層與真實瀏覽器

正常套件 48 項：原有進程內 44 項、真實客戶端清理 2 項、驗收變異迴歸 2 項；
獨立答案 3 項。先讀直接構造 TestClient 的普通測試，再學
fixture。每項建立新的 app/store；overrides fixture 用 finally 恢復原映射，
鍵必須是原函數對象。替身不能證明原依賴正常。TestClient 運行真實應用，但
不經過 Uvicorn 網絡端口。

```bash
uv run --locked python -m pytest -q tests/test_first_request.py
uv run --locked python -m pytest -q solutions/test_independent.py
uv run --locked python -m pytest -q experiments/test_fixture_failure.py
uv run --locked python live_httpx.py --port 8006
uv run --locked python -m http.server 5506 --bind 127.0.0.1 --directory browser
```

故障實驗刻意退出 1，結果為 **1 failed, 1 passed**：斷言失敗後，fixture 仍
恢復了**同一個** app 的覆寫。testpaths 將它排除在正常套件之外，不用 xfail
掩蓋失敗；這個有序探針也不是普通獨立測試的推薦寫法。
HTTPX 命令要求 Uvicorn 終端仍在運行；瀏覽器明確使用 API 端口 8006。

打開 http://127.0.0.1:5506，點擊 Run browser check，預期 POST 201、GET 200、
嚴格輸入 422 和 DELETE 204 清理。瀏覽器會實際預檢並執行 CORS 限制，
TestClient/HTTPX 不會。另開終端在 5507 提供同一 browser 目錄，從該來源打開，
預期 fetch 失敗且沒有新任務；Network 面板裡應看到 OPTIONS 被拒絕。
Python 客戶端仍可不帶 Origin 訪問，說明 CORS 不是認證。不能用 no-cors、
任意來源或關閉瀏覽器安全性“修復”。最後 Ctrl-C 停兩個靜態服務和 Uvicorn。

## 有界維護迴歸

```bash
uv run --locked python -m pytest -q tests/test_live_client_cleanup.py
```

預期 `2 passed`。兩項在操作系統分配的本地端口啟動自有故障服務器，運行真實
客戶端。首個 DELETE=503 不能跳過第二個 ID；只剩第一個且客戶端非零退出。
第二項還讓主體失敗，並檢查原 traceback 保留。finally 停自己的服務器，
不接觸用戶已有服務。這個維護工具不是獨立練習先修，不要求異步測試代碼。

```bash
uv run --locked python -m pytest -q tests/test_patch_readback_regression.py
```

預期 `2 passed`。只在可丟棄副本植入“空 PATCH 返回舊記錄、存儲卻變默認值”
的 mutant。基礎 note 三態子運行必須在後續 GET 處失敗（`1 failed, 2 passed`），
獨立空 PATCH 子運行同樣失敗（`1 failed`）。外層只有觀察到讀回斷言抓住缺陷
才通過，收集/導入錯誤不算。canonical 服務文件不變。這些外層用例已計入 48 項。

## 打包、暫停恢復與證據

只有旁邊 allowlist 中的文件進入下載包。明確排除 .venv、__pycache__、
.pytest_cache、.env/.env.*、日誌、憑證、編輯器狀態、臨時文件及本地緩存。
不要遞歸壓縮目錄。包含 uv.lock，但不包含解釋器安裝和緩存。三語 README
保持命令與輸出不變。

暫停記錄工作目錄、版本、最後命令及真實結果、服務 PID/端口與是否停止、
數據現狀、未解決失敗及下次第一步。恢復先鎖定同步與正常測試，再重放具體
失敗請求。Python 語法通過不是 HTTP 驗收。

SOURCES.md 記錄實時核驗的一手來源與版本/scope 細節。倉庫可選維護腳本
`scripts/test-js2py-http-foundations.py` 檢查 allowlist 乾淨副本、兩套測試、
預期失敗、真實本地服務、資源發送時序和進程清理；它不是讀者先修，也不替代
真實瀏覽器檢查。生產、數據庫、TLS、壓測行為均不在本實驗的驗證範圍。
