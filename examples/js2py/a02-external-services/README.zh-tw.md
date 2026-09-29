# A02 — 外部服務生命週期

核驗日期 2026-09-28。這是位於 S03 後的獨立本地實驗，不是完整 capstone，
不導入其他章節源碼。前置為 Python 函數、異常、上下文管理器、測試和已有的
同步 API/SQL/認證基礎；A02 另以 A01、L14、H05 為前置。

## 從乾淨下載復現

解壓後進入 `a02-external-services`；倉庫中進入 `examples/js2py/a02-external-services`。
固定 CPython 3.13.15、uv 0.12.13、pytest 8.4.2，先安裝指定 uv，本實驗不替你升級工具。
FastAPI 0.135.1, Uvicorn 0.42.0, Pydantic 2.12.5, HTTPX 0.28.1, AnyIO 4.12.1, Starlette 0.52.1.
Web 框架沿用 H03–H06 基線，生命週期依賴沿用 H05–H06。
真實 public-PyPI lock 含解析結果和製品哈希，requires-python 只接受 3.13，
`tool.uv.package=false` 表示直接運行本地源碼，不安裝本項目為包。
不要刪鎖或無聲升級框架。

```bash
# Run from the extracted a02-external-services directory.
set -eu
export PATH="$HOME/.local/bin:$PATH"
export UV_PYTHON_INSTALL_DIR=/tmp/langshift-js2py-python-20260928
export UV_CACHE_DIR=/tmp/langshift-js2py-uv-cache-20260928
uv --version
uv python install 3.13.15
uv sync --locked
uv run --locked python --version
uv run --locked python socket_lab.py
uv run --locked python -m pytest -q
uv run --locked python -m pytest -q solutions
```

兩個 /tmp 目錄隔離解釋器與下載緩存，不保存業務數據。安裝鎖定公共依賴需要聯網，
實驗運行不訪問收費/第三方服務、不發送用戶數據。

## 穩定演示輸出

輸出以 `expected-socket-output.txt` 為源，實際運行必須匹配。

```text
socket: normal hint available; upstream connection reused
socket: unavailable -> unavailable; core read ok
socket: malformed -> unavailable; core read ok
socket: wrongshape -> unavailable; core read ok
socket: oversized -> unavailable; core read ok
socket: slow -> unavailable; core read ok
socket: core create/update/read/delete finished while upstream held
socket: lifespan client closed
```

主測試 **32 passed**，獨立答案測試 **4 passed**。耗時不是正確性斷言。
除故意收集警告的診斷外，警告視為錯誤；主測試不會偷偷包含答案測試，兩個命令都要跑。

## 文件地圖與真實證據

- `lifecycle.py`：迴環 allowlist、共享客戶端、階段超時、有界清理保護。
- `app.py`：顯式 lifespan、合成內存 CRUD、單獨的可選提示接口。
- `service.py`：整次操作預算、共享准入上限、最多兩次只讀 GET、正文上限、嚴格驗證、脫敏降級與取消傳播。
- `faults.py`：測試專用 ok/unavailable/flaky/malformed/wrongshape/oversized/slow/hold 場景。
- `socket_lab.py`：兩個綁定自動分配 127.0.0.1 端口的真實 Uvicorn 服務。
- `tests/test_service.py`：27 項政策/ASGI/診斷測試；替身不能證明真實網絡計時。
- `tests/test_socket.py`：5 項真實 TCP 測試，正常/異常/取消後的對端 EOF、關閉後拒絕使用、取消單次借用後容量仍可複用。
- `solutions/receipts.py` 及測試：丟回覆與冪等練習，以及重啟不持久的反證。

手動服務器分別開兩個終端，從同一個實驗根啟動：

```bash
uv run --locked uvicorn faults:create_fault_app --factory --host 127.0.0.1 --port 8766
uv run --locked uvicorn app:create_app --factory --host 127.0.0.1 --port 8765
```

默認上游端口 8766，只用合成任務文本；/control 只供測試。結束時只在自己的兩個終端按 Ctrl-C。
端口衝突時用 socket_lab.py，不殺不認識的進程；自動實驗只停止自己持有的 Server 並關閉自己的 socket。

## 故障、練習與恢復

`uv run --locked python -m errors.config` 應退出 1，最後一行異常脫敏；源碼中的 URL 明確為假。
原始 traceback 仍可能帶源碼行，不能公開返回。
`uv run --locked python -m errors.untrusted` 應退出 1 並報告 ValidationError，說明可解析 JSON 不等於可信數據。

引導修改：僅一次嘗試、一個併發操作；更新政策次數斷言，不篡改替身行為。
獨立變式：以固定冪等鍵重現回覆丟失，同 key/正文只產生一次效果，不同正文衝突，取消不重試，重啟揭示內存賬本不持久。

恢復卡：當前文件、版本、最後成功命令、32+4 中已通過哪組、首個失敗場景、下次只跑哪個測試。
app.state 缺失先查 lifespan；正常請求報 client closed 則查是否請求誤關共享對象。

## 安全與未證明邊界

只接受明確的 http://127.0.0.1:<port>，無真實憑證、用戶數據、收費服務或環境秘密讀取，不跟隨重定向，禁用 HTTPX 代理繼承。
CRUD 僅在內存、重啟丟失且沒有認證授權，不能公開暴露或替代 capstone 的 SQL/權限設計。

讀取空閒超時有真實 socket 證據；connect/write/pool 故障政策含替身測試，不是所有網絡階段已實際驗證。
沒有驗證 TLS、真實 DNS、HTTP/2、多 worker 容量、進程強殺或其他 AnyIO 後端。
測試顯式取消擁有者 Task，不聲稱每次 HTTP 斷開都會取消 handler。
BackgroundTasks 與內存隊列不是持久投遞系統。

## 下載與單一源碼約定

DOWNLOAD-ALLOWLIST.json 與倉庫同名實驗 -files.json 列表一致，只打包這些普通文件。
不包含環境、緩存、憑證或真實業務數據；教材 loader 讀取相同源文件。
sources.json 記錄官方依據與核驗日期，uv.lock 中製品哈希來自 public PyPI 實際解析。
