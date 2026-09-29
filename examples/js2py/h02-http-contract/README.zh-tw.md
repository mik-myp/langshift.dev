# H02：與 H04–H06 對齊的 HTTP 契約

版本 `h02-task-contract-v2-h04-aligned`。核驗日期 2026-09-28。**本實驗仍只有契約樣本、純函數預覽和靜態服務，沒有任務 CRUD。**

## 主線與可選加固分開

前置 H01 的進程、請求、端口與可信邊界。當前核心為 `/tasks` 與 `id/title/minutes/done/note`：title 保留原字形/首尾空白但不能全空白，minutes 為必填嚴格非負整數，done 為嚴格布爾值默認 false，note 可空默認 null，id 由服務生成。PATCH 省略字段保留、顯式 note=null 清除、0/false 應用；空 PATCH 合法無變化。

分頁為 limit 默認20、最大100，offset默認0且非負，按id排序，輸出 `items/limit/offset/total`，沒有 next_offset 或狀態篩選。404 是文本 detail；422 是 detail 數組，畸形 JSON 也為422。title/minutes/done 不接受 null，未知正文鍵拒絕，輸出不洩漏 internal_tag。

完整離線約定見 `CONTRACT.zh-cn.md`（英文 `CONTRACT.md`、繁體 `CONTRACT.zh-tw.md`）。項目、成員、身份和數據庫關係屬於未來 D/S 演進，不是當前字段。HEAD、未知query拒絕、413/415、自定義錯誤、Location與生產脫敏均不作為H04已經兌現的承諾；實際差距見 `gaps/h04-observations.json`。

## 文件語義

24份 `public/exchanges` 樣本彼此獨立。`kind` 標註擬定；`precondition.seed_tasks` 記錄初始條件；`request` 和 `response` 描述交互，不是在線API額外返回的包裝。request.body 為對象時按 JSON 編碼；malformed-json 的字符串表示原始待發送文本，不再包一層JSON引號。204的response.body=null是“沒有正文”的樣本標記，不代表傳輸四個字符null。

下載創建樣本實際HTTP200不等於執行創建並得到201；讀取刪除樣本不會刪除任務。wire文件是省略Date/長度等細節的可讀摘錄，不是抓包或HTTP編碼器。check_example只檢查樣本不變量，preview_page處理已解析的Python值，兩者不是H04模型驗證或HTTP解析器。

## 環境與復現

固定 CPython3.13.15、pytest8.4.2，requires-python `>=3.13,<3.14`，package=false；實測 uv0.12.13、macOS、curl8.7.1。H02不安裝FastAPI；維護者另用隔離副本核對H04的FastAPI0.135.1/Uvicorn0.42.0/Pydantic2.12.5。沒有修改共享H04源碼或鎖。

倉庫用戶從根目錄進入實驗；下載用戶進入解壓的h02-http-contract，從uv sync開始。

```bash
cd examples/js2py/h02-http-contract
pwd
uv sync --locked --default-index https://pypi.org/simple
uv run --locked python --version
uv run --locked python contract_examples.py
uv run --locked python inspect_transport.py
uv run --locked python -m pytest -q
uv run --locked python -m pytest -q solutions/test_review_cases.py
```

契約腳本最後輸出：

```text
checked 24 proposed exchanges; no CRUD requests executed
```

標準47項（43項樣本/計算、4項真實HTTP），獨立5項。真實傳輸輸出：

```text
real GET example: HTTP 200; proposed POST: 201
real GET tasks: HTTP 404
real POST tasks: HTTP 501; no CRUD implemented
real HEAD example: HTTP 200; body bytes=0
real GET with Origin: HTTP 200; allow-origin=False
service_alive=True
owned_service_stopped=True
```

這些HEAD結果來自標準庫靜態工具，不是H04任務路由；H04 HEAD /tasks實測405。不要把一個工具的能力自動遷移為另一個應用的保證。

## 兩個終端的真實請求

A、B都在實驗根。A前臺啟動：

```bash
uv run --locked python -m http.server 8767 --bind 127.0.0.1 --directory public
```

`-m` 運行標準庫模塊；8767是監聽端口；`--bind` 限定loopback；`--directory public` 相對A啟動目錄。等待請求時不返回提示符是正常行為。

B運行：

```bash
curl --noproxy '*' --max-time 3 --include 'http://127.0.0.1:8767/exchanges/create-ok.json'
curl --noproxy '*' --max-time 3 --include 'http://127.0.0.1:8767/tasks'
curl --noproxy '*' --max-time 3 --include --header 'Content-Type: application/json' --data-binary @requests/create.json 'http://127.0.0.1:8767/tasks'
curl --noproxy '*' --max-time 3 --include --fail-with-body 'http://127.0.0.1:8767/tasks'
echo $?
```

狀態依次200/404/501/404，最後curl退出22。curl是客戶端；`--noproxy '*'` 繞過代理並用引號防shell展開；`--max-time 3` 限整輪等待；`--include`顯示頭與正文；`--header`添加頭；`--data-binary @...`從B目錄原樣讀取文件並默認POST；`--fail-with-body`保留HTTP錯誤正文併產生非零退出。默認curl收到HTTP錯誤仍可退出0，不能把退出碼等同HTTP狀態。

```bash
curl --noproxy '*' --max-time 3 --include --header 'Origin: https://untrusted.invalid' 'http://127.0.0.1:8767/exchanges/create-ok.json'
curl --noproxy '*' --max-time 3 --include --request OPTIONS --header 'Origin: http://127.0.0.1:5173' --header 'Access-Control-Request-Method: POST' --header 'Access-Control-Request-Headers: content-type' 'http://127.0.0.1:8767/tasks'
```

分別200且無Allow-Origin、501。`--request OPTIONS`指定方法；頭中域名不是連接目標，沒有訪問它。curl不執行瀏覽器響應共享政策，因此不證明瀏覽器CORS成功。CORS也不是認證、授權或完整CSRF防護。

回A按Ctrl+C，只停止自己的前臺實例。自動工具使用另一個分配的loopback端口，只清理自己的子進程，不會停手動A。端口衝突時辨認自有實例或換端口，禁止按端口殺陌生進程。只公開public，不放.env、工程根、用戶目錄、符號鏈接或真實數據。

## 意圖失敗與獨立變式

```bash
uv run --locked python -m pytest -q errors/test_wrong_contract.py
```

預期1項斷言失敗、退出1：錯誤斷言把204寫成200。正確修復是斷言204與無正文、讓客戶端跳過JSON，而非改壞樣本。錯誤文件不在默認tests中。失敗是測試斷言，不是HTTP500。

先自寫第二頁(limit1/offset1)、末頁外空頁、PATCH省略note、顯式null四個正常交互，再寫minutes=null與limit101兩個422；解釋空PATCH不變而0/false是真實設置。solutions給出五項純計算/一致性測試與六份完整交互，不能把它們叫在線CRUD測試。

## 恢復與已驗證邊界

暫停記錄v2契約版本、修改樣本、目錄、自有服務終端/端口、最後命令、47+5項結果與下次第一步；停止服務。恢復先跑離線檢查和inspect_transport，再手動請求，不推斷有以前創建的任務。

當前快照實測：H02樣本、分頁、獨立變式、意圖失敗、靜態傳輸；維護者還在隔離H04副本核對24個核心交互與5項差距。HEAD405、未知query被忽略、媒體類型錯誤422而非415、超過64KiB的合法JSON仍201是差距觀察，不是新增核心承諾。源摘要保存在gaps記錄中。

未實現/未驗收：H02 CRUD、完整schema、登錄/權限、數據庫、併發冪等、正文限額執行、生產脫敏、真實瀏覽器CORS、TLS、公網、Linux/Windows執行、最終ZIP與全站集成。發佈文件由外部同名-files.json顯式列出，不含環境、緩存、日誌或憑證。

## 一手資料

2026-09-28核對：[RFC9110](https://www.rfc-editor.org/rfc/rfc9110.html)、[RFC5789](https://www.rfc-editor.org/rfc/rfc5789.html)、[Pydantic嚴格模式](https://github.com/pydantic/pydantic/blob/v2.12.5/docs/concepts/strict_mode.md)、[響應模型](https://fastapi.tiangolo.com/tutorial/response-model/)、[部分更新](https://fastapi.tiangolo.com/tutorial/body-updates/)、[錯誤處理](https://fastapi.tiangolo.com/tutorial/handling-errors/)、[Fetch/CORS](https://fetch.spec.whatwg.org/#http-cors-protocol)、[http.server](https://docs.python.org/3.13/library/http.server.html)、[http.client](https://docs.python.org/3.13/library/http.client.html)、[curl](https://curl.se/docs/manpage.html)。
