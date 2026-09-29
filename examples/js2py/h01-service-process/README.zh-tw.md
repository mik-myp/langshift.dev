# H01：從客戶端到持續運行的服務

狀態：本地實驗，不是任務 API 或可部署後端。核驗日期 2026-09-28。

## 目標與範圍

前置為 L10 本地工程和 L14 資源生命週期。你將啟動一個進程、觀察 loopback 監聽、追蹤請求到文件的路徑，區分請求完成與進程退出，定位 404/連接失敗/端口衝突，並只停止自己的服務。不要求實現 HTTP 服務器、FastAPI、數據庫、認證或異步。

只公開 `public` 或參考 `solutions/public`。不要公開工程根、用戶目錄、憑證、`.env` 或符號鏈接。`http.server` 會跟隨符號鏈接且可能列出目錄，不是安全沙箱；loopback 不是身份驗證。

## 環境與工作目錄

固定 CPython 3.13.15（`.python-version`），範圍 `>=3.13,<3.14`；開發依賴 pytest 8.4.2；實測 uv 0.12.13、macOS、curl 8.7.1。無第三方運行依賴。命令為 macOS/Linux shell；未驗收 Windows 的終端與信號行為。

倉庫用戶先從倉庫根進入下面目錄。下載用戶進入解壓後的 `h01-service-process`，從 `uv sync` 開始。

```bash
cd examples/js2py/h01-service-process
pwd
uv sync --locked --default-index https://pypi.org/simple
uv run --locked python --version
uv run --locked python one_shot.py
uv run --locked python observe.py
uv run --locked python -m pytest -q
uv run --locked python -m solutions.observe_health
uv run --locked python -m pytest -q solutions/test_health.py
```

`observe.py` 的穩定輸出：

```text
200 hello from the service
404 missing
200 hello from the service
request_done_process_alive=True
process_stopped=True
```

標準 13 項、獨立參考 2 項通過。獨立參考訪問 health 返回 `ready`，404 後再請求仍成功。自動工具只監聽 `127.0.0.1`，讓操作系統選擇端口，並在 finally 中清理自己創建的子進程。測試證明列出的本地行為，不證明生產併發、外網安全或持久化。

## 兩個終端，真實請求

A、B 都位於實驗根。A 前臺啟動：

```bash
uv run --locked python -m http.server 8765 --bind 127.0.0.1 --directory public
```

`-m` 運行標準庫模塊；`8765` 為端口；`--bind` 限定 loopback；`--directory` 指公開目錄，相對 A 的啟動工作目錄。提示符不回來是服務等待請求的正常行為。

B 發出請求：

```bash
curl --noproxy '*' --max-time 3 --verbose 'http://127.0.0.1:8765/hello.txt'
curl --noproxy '*' --max-time 3 --include 'http://127.0.0.1:8765/not-here.txt'
echo $?
uv run --locked python client.py 8765 /hello.txt
```

curl 是客戶端，不監聽服務端口。`--noproxy '*'` 繞過代理，引號防止 shell 展開星號；`--max-time 3` 限制整輪傳輸；`--verbose` 把連接/頭部診斷寫到標準錯誤；`--include` 把響應頭和正文一起顯示。先看到 200 與 `hello from the service`，再看到 404 的 HTML 錯誤頁。默認 curl 收到 HTTP 錯誤仍可退出零；`echo $?` 是命令退出狀態，不是 HTTP 狀態。Python 客戶端成功為零、HTTP 錯誤退出 2、連接異常退出 1。

回到 A 按 Ctrl+C，只停止這個前臺實例。B 再請求原 URL，在端口無人接管的實測條件下 curl 退出 7，沒有 HTTP 響應。恢復用原啟動命令。禁止 `killall`、按端口殺陌生進程、開放 `0.0.0.0` 或加公網隧道。

## 失敗定位與練習

- `Address already in use` 是啟動階段獲取監聽失敗。確認自己的舊實例，不能確認就換 `8766` 並同步所有客戶端；不停止不明進程。
- 404 表示有 HTTP 響應，檢查路徑與公開目錄，而非重裝 Python。把公開目錄換為 `solutions/public` 會讓 `/hello.txt` 404、`/health.txt` 200。
- 連接失敗發生在 HTTP 響應之前，檢查自己的進程、主機和端口。停止自有服務再重試可以復現，不探測他人的服務。
- 獨立任務：用另一個公開目錄和端口完成 health 成功、缺失路徑失敗、note 成功，並證明舊 hello 不共享。先自己完成，再看 `solutions`。

解釋題答案：客戶端退出只結束自己；服務繼續持有監聽資源。404 不能證明資源存在，也不能單獨證明響應者是預期實例。前端禁用輸入框無法約束其他客戶端；後續必須由服務端驗證與授權。

## 暫停恢復與文件說明

記錄工作目錄、公開目錄、端口、擁有服務的終端、最後成功/失敗命令、失敗層次、13+2 項測試結果與下次第一步；暫停前停止自己的實例。恢復先跑 `observe.py`，再重做手動成功/失敗/成功，不拿舊筆記 PID 隨意殺進程。

`client.py` 是單次 HTTP 客戶端；`observe.py` 是生命週期觀察；`tools/owned_server.py` 是有超時的測試基礎設施，不是學生必須重建的服務器實現。它只使用標準庫 CLI，絕不按端口掃描或停止其他程序。`tests` 是默認套件，`solutions` 是獨立參考。下載由外部同名 `-files.json` 顯式清單生成；不包含 `.venv`、緩存、臨時日誌或憑證。

## 一手資料

2026-09-28 核對：[http.server](https://docs.python.org/3.13/library/http.server.html)、[http.client](https://docs.python.org/3.13/library/http.client.html)、[subprocess](https://docs.python.org/3.13/library/subprocess.html)、[curl](https://curl.se/docs/manpage.html)、[RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)、[IANA loopback](https://www.iana.org/assignments/iana-ipv4-special-registry/iana-ipv4-special-registry.xhtml)、[WHATWG URL](https://url.spec.whatwg.org/)。沒有驗收公網、TLS、瀏覽器跨源策略、數據庫或生產部署。
