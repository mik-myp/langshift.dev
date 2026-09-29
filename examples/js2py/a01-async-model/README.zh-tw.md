# A01 — Python 異步執行模型

核驗日期 2026-09-28。這是位於 S03 後的獨立本地實驗，不是完整 capstone，
不導入其他章節源碼。前置為 Python 函數、異常、上下文管理器、測試和已有的
同步 API/SQL/認證基礎；A02 另以 A01、L14、H05 為前置。

## 從乾淨下載復現

解壓後進入 `a01-async-model`；倉庫中進入 `examples/js2py/a01-async-model`。
固定 CPython 3.13.15、uv 0.12.13、pytest 8.4.2，先安裝指定 uv，本實驗不替你升級工具。
沒有第三方運行時依賴。
Web 框架沿用 H03–H06 基線，生命週期依賴沿用 H05–H06。
真實 public-PyPI lock 含解析結果和製品哈希，requires-python 只接受 3.13，
`tool.uv.package=false` 表示直接運行本地源碼，不安裝本項目為包。
不要刪鎖或無聲升級框架。

```bash
# Run from the extracted a01-async-model directory.
set -eu
export PATH="$HOME/.local/bin:$PATH"
export UV_PYTHON_INSTALL_DIR=/tmp/langshift-js2py-python-20260928
export UV_CACHE_DIR=/tmp/langshift-js2py-uv-cache-20260928
uv --version
uv python install 3.13.15
uv sync --locked
uv run --locked python --version
uv run --locked python app.py
uv run --locked python -m pytest -q
uv run --locked python -m pytest -q solutions
```

兩個 /tmp 目錄隔離解釋器與下載緩存，不保存業務數據。安裝鎖定公共依賴需要聯網，
實驗運行不訪問收費/第三方服務、不發送用戶數據。

## 穩定演示輸出

輸出以 `expected-output.txt` 為源，實際運行必須匹配。

```text
creation: called:no-body-yet | A:start | A:end
sequential: A:start | A:end | B:start | B:end
scheduled: A:start | B:start | owner:both-entered | B:end | A:end
blocking: sync:start | sync:end | callback:ran | owner:resumed
offloaded: loop:responsive-while-thread-waits | thread:returned
cancelled: file:opened | file:closed | owner:cancelled
timeout: file:opened | file:closed | owner:timeout
bounded: peak=2 active=0
```

主測試 **19 passed**，獨立答案測試 **5 passed**。耗時不是正確性斷言。
除故意收集警告的診斷外，警告視為錯誤；主測試不會偷偷包含答案測試，兩個命令都要跑。

## 文件地圖與解讀

- `comparison.py` / `comparison.js`：完整 Python/JS 調用與執行對照。
- `scheduling.py`：創建、順序 await、顯式調度、阻塞與明確收尾的線程橋接。
- `ownership.py`：取消/超時後的真實臨時文件釋放。
- `capacity.py`：用 entered/release 門閂證明准入上限。
- `app.py`：上面的完整演示。
- `tests/test_model.py`：事件順序、文件關閉與拒絕寫入、許可複用、真實失敗命令。
- `solutions/batch.py` / `solutions/test_batch.py`：獨立、有界、可取消的批處理。

JS 對照可選用已有 Node，不要求為 Python 測試安裝 Node：

```bash
node comparison.js
uv run --locked python comparison.py
```

預期輸出為 expected-javascript.txt、expected-python.txt。Python 調 coroutine 不啟動函數體，默認工廠的 Task 顯式調度工作，
直接 await 順序推進，已就緒對象的 await 不必讓出。不要拿不穩定耗時推斷事件循環進度。

## 真實失敗與練習

`uv run --locked python errors/reuse.py` 先打印 42，再以 RuntimeError 退出 1。
`uv run --locked python errors/forgotten.py` 收集真實未 await 警告，工作 events 仍空。
`uv run --locked python errors/swallow.py` 雖退出 0，卻顯示 pretend-success 和 cancelled=False，是語義失敗。
主測試在獨立子進程核驗這些命令。

引導練習改上限 1 和 3，用 peak 與 active 歸零證明，不比耗時。
獨立變式先整批驗證再產生效果，最多八項，保持輸入結果順序，限制併發和預算，錯誤/超時/取消後收尾全部孩子。
答案測試檢查沒有遺留 Task；按輸入順序觀察不是 fail-fast 監督。

恢復卡：當前文件、Python/uv 版本、最後成功命令、19+5 中已通過哪組、自己的需求改動、首個反例和下一條聚焦命令。
不要增加任意 sleep 修復順序，也不要刪除其他環境或改共享配置。

## 安全與邊界

僅打開臨時文件並運行一個明確等待結束的本地工作線程，不訪問外部服務、不需要憑證。
取消不能強殺線程或撤銷既有效果；事件循環阻塞時不能保證絕對牆鍾截止。
Semaphore 限制准入，不限制無限創建 Task 的內存開銷。沒有性能、生產隊列、異步數據庫或部署承諾。

## 下載與單一源碼約定

DOWNLOAD-ALLOWLIST.json 與倉庫同名實驗 -files.json 列表一致，只打包這些普通文件。
不包含環境、緩存、憑證或真實業務數據；教材 loader 讀取相同源文件。
sources.json 記錄官方依據與核驗日期，uv.lock 中製品哈希來自 public PyPI 實際解析。
