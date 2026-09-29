# O03 HTTPS、入口代理與生產邊界

前置 O02。診斷工具只在127.0.0.1上運行；沒有真實認證/任務數據庫，不能公開。S階段實際方案是不透明Authorization Bearer會話，DB摘要+expiry/revoked+auth_version，不用JWT或認證Cookie；本工具僅證明虛構頭被傳遞，絕不證明認證成功。

## 環境與恢復

核驗日期：**2026-09-28**。需要普通 POSIX 賬戶；不以 root 運行權限實驗。CPython **3.13.15**、uv **0.12.13**、pytest **8.4.2**。`.python-version` 選解釋器，pyproject 聲明 `>=3.13,<3.14`，uv.lock 鎖依賴；`[tool.uv] package=false` 表示不打包這個練習為可發佈 Python 包。

Web 基線：FastAPI **0.135.1**、Uvicorn **0.42.0**、Pydantic **2.12.5**、HTTPX **0.28.1**、Starlette **0.52.1**、AnyIO **4.12.1**；沒有前端依賴。

倉庫用戶從倉庫根目錄執行下列 cd；ZIP 用戶直接進入解壓後的同名實驗根目錄，裡面應有 pyproject.toml。`--locked` 拒絕悄悄更新鎖。

```bash
cd examples/js2py/o03-https-production
pwd
uv --version
uv sync --locked
uv run --locked python --version
```

維護者鎖文件已用 `uv lock --default-index https://pypi.org/simple` 實際生成。讀者恢復不需要重新解析。環境與緩存不進清單/ZIP，所有數據實驗用自己創建的臨時目錄。

額外系統工具：OpenSSL3.x支持 req -addext/-noenc（本輪3.6.4）、curl（本輪8.7.1）。不自動安裝系統軟件。certificates.py僅在自有/tmp目錄生成一天有效的臨時CA與lab.test葉證書，目錄0700/文件0600，不安裝系統信任、不打包、不打印私鑰。

```bash
openssl version
curl --version
uv run --locked python tls_lab.py
uv run --locked python -m pytest -q
uv run --locked python -m pytest -q solutions/test_origin_policy.py
uv run --locked python check_config.py
```

```text
trusted_ca_https=200
unknown_ca_curl_exit=60
wrong_hostname_curl_exit=60
edge_overwrites_forged_forwarding=True
authorization_forwarded_not_authenticated=True
untrusted_proxy_headers_ignored=True
trusted_loopback_direct_spoof_possible=True
sanitized_error=500
sanitized_validation=422
teaching_edge_body_limit=413
owned_processes_stopped_and_temp_keys_removed=True
```

## 雙終端交互與停止

終端A運行下列命令。--serve保持前臺；--port 0讓OS選空閒端口。把程序實際打印的export CA和export PORT行復制到終端B；CA是公開信任材料路徑，不是私鑰。終端B仍在實驗根目錄運行curl。--resolve僅覆蓋這一次客戶端的DNS映射，保留SNI/Host；--cacert啟用指定CA校驗，--noproxy避開外部代理，--max-time限制等待，--include顯示響應頭，-H添加請求頭。

```bash
uv run --locked python tls_lab.py --serve --port 0
```

```bash
curl --silent --show-error --include --max-time 5 --noproxy '*' --resolve "lab.test:$PORT:127.0.0.1" --cacert "$CA" -H 'Authorization: Bearer demo-not-a-valid-session' "https://lab.test:$PORT/probe"
```

預期200、scheme=https、authorization_present=true，但並未認證。去掉--cacert或改URL與resolve名字為wrong.test，各自curl exit60；嚴禁用-k算驗收。終端A的Ctrl+C停止自有後端/邊緣並刪除臨時密鑰；舊CA路徑隨後失效，下次啟動重新複製。自動模式同樣清理，絕不killall。

## 機制與故意缺口

edge.py是有界標準庫教學轉發器，不是生產HTTP解析器。只接受限定請求頭，覆蓋Forwarded類信息；4096字節body限制返回413僅對本邊緣成立，不替H04/S03承諾策略。app.py返回安全500與loc/type-only422，不回顯輸入/traceback，日誌只安全事件和隨機id；/fail只供本地故障實驗。

關閉代理信任會忽略偽造頭；通過邊緣會被覆蓋；但受信127.0.0.1上游可被同機其他進程直連偽造。該觀察是真實殘餘風險，必須通過實際部署隔離解決，不能用allow-ips=*修URL。TLS不負責查會話、成員授權或撤銷。

精確來源CORS只允許演示GET/POST及Authorization/Content-Type/Idempotency-Key；真實S API另需完整方法策略。allow_credentials=False、不用Cookie；CORS不是認證，curl不執行瀏覽器讀取限制。若改Cookie須重新評估CSRF/SameSite/Secure/HttpOnly/來源和反CSRF機制。真實瀏覽器未驗收。

## Caddy/公網（未實跑）

Caddyfile.local使用同主機loopback上游8034和顯式TLS_CERT/TLS_KEY路徑；production.template保留api.example.invalid，不可直接發佈。caddy缺失，所以只執行check_config文本不變量檢查，沒有caddy validate/運行證據。若在自己的受控主機準備固定Caddy、獨立證書與目標應用，可先單獨啟動下面的本地診斷上游供配置測試；這不是生產服務。需要自行準備證書路徑再驗證本地配置，不得借用用戶真實私鑰。

```bash
uv run --locked python -m uvicorn app:create_app --factory --host 127.0.0.1 --port 8034 --proxy-headers --forwarded-allow-ips 127.0.0.1 --no-access-log
caddy validate --config Caddyfile.local --adapter caddyfile
```

上面第一條是前臺命令，第二條在另一終端且已準備證書環境時運行；結束第一條用Ctrl+C。不同容器不能用彼此的loopback通信；拓撲改變須重審上游/信任邊界。公網DNS、公簽證書籤發續期、訪問限制、完整S03認證撤銷與DB ready、請求大小和登錄節流、發佈回退與備份恢復都仍待驗收；不創建任何公開資源。

## 獨立需求

允許frontend.lab.test:8444與admin.lab.test:8445兩個精確HTTPS來源；錯端口、HTTP、惡意域名後綴與null預檢拒絕。不用Cookie，不把無Origin直接調用稱為認證。先寫實現與測試，再看solutions/origin_policy.py的7個獨立case。

## 環境矩陣（機器可讀版本：ENVIRONMENT.json）

| 狀態 | 證據與門檻 |
| --- | --- |
| 已實際運行 | 臨時CA/葉證書與權限、curl --cacert成功及未知CA/錯主機名exit60、loopback TLS、轉發頭覆蓋/忽略與同機直連偽造缺口、虛構Authorization傳遞、脫敏500/422、教學413、CORS頭、清理。 |
| 本機不可運行 | 無Caddy、無受控Linux/容器環境；未提供用戶域名、主機或生產秘密。 |
| 用戶需自備 | 受控主機與固定反代版本、自有域名/DNS、防火牆/挑戰端口許可、生產秘密與證書持久存儲、實際瀏覽器前端及完整S03服務。 |
| 待環境驗收 | caddy validate與運行、真實A/AAAA/公網連通、公簽證書申請續期、上游不可繞過/多代理信任、真實瀏覽器、Cookie變更時CSRF重評估、S03撤銷/授權/DB ready、生產body限制/登錄節流/哈希容量、遷移回退與備份恢復。 |

本輪標準 **17**、獨立 **7** 個測試通過。源碼與文稿 `implemented`；矩陣中的外部環境 `environment_pending`，不是整體部署通過。普通 macOS 測試不能代替 Linux/容器/公網或 Windows 證據。

## 恢復學習與排錯記錄

記錄源碼/鎖摘要、cwd、工具版本、最後成功命令、失敗階段與分類、實際測試數、環境矩陣和下次第一步。不要記錄完整環境、真實 token、數據庫 URL 或私鑰。恢復先 `uv sync --locked`，再跑標準與自己寫的獨立測試。只有參考答案通過，不代表你能獨立實現。

## 一手資料

SOURCES.json 保存 2026-09-28 核驗的官方地址、作用範圍、HTTP獲取結果與SHA-256摘要。章節正文解釋每個機制，README 提供離線運行入口。這裡沒有自動創建生產資源、安裝系統軟件或接受服務條款。
