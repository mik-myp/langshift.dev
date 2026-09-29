# s01-identity：完整獨立本地實驗

[English](README.md) · [简体中文](README.zh-cn.md)

## 1. 契約與起點

這是教材 S01 的獨立下載包，不從別章導入源碼，不需要前端依賴。讀者已學 D06 的 PostgreSQL、事務、遷移與 fixture；S02 還依賴 S01 身份機制，S03 還依賴 S02 對象權限。先根據本 README 預測結果，再用真實 HTTP 和數據庫驗證；編譯成功不算 API 驗收。完整機制與摺疊答案見對應教材章節。

所有實驗只監聽 127.0.0.1；PostgreSQL 只使用本程序的私有 Unix socket。**不得將實驗直接暴露公網，不得連接或停止用戶現有數據庫。** 本地 trust 依賴私有目錄與本機用戶邊界，不代表生產數據庫認證設計。

基線核驗 **2026-09-28**：CPython 3.13.15、uv 0.12.13、FastAPI 0.135.1、Uvicorn 0.42.0、Pydantic 2.12.5、SQLAlchemy 2.0.54、Alembic 1.20.0、psycopg[binary] 3.3.6、PostgreSQL 18.6、argon2-cffi 25.1.0、pytest 8.4.2。公開 PyPI 的 uv.lock 固定實際依賴，不宣稱最新；Python 範圍 >=3.13,<3.14，uv 不將實驗作為發佈包安裝。

## 2. 文件職責

| 文件 | 職責 |
| --- | --- |
| pyproject.toml / uv.lock / .python-version | 聲明、完整解析與解釋器 pin |
| migrations / alembic.ini | 從空庫到本章的真實遷移；001–003 完整沿用 D |
| models.py / schemas.py | 數據庫存儲與請求/公開模型分開 |
| db.py / security.py | 每請求事務入口、Argon2id、會話查驗/撤銷；不是全局 Session |
| app.py / serve.py | HTTP 適配、錯誤脫敏與只監聽迴環的進程入口 |
| admin.py / client.py | 受控開通與 getpass 客戶端；不打印密碼/Bearer |
| labdb.py | 自建、核對歸屬、重啟/停止獨佔臨時 PG 集群 |
| tests / solutions | 真實 PG/HTTP 驗收和獨立變式答案 |
| SOURCES.md / VERIFICATION.md | 官方核驗與實際證據/未覆蓋面 |

## 3. 工作目錄與首次啟動

在解壓後的 `s01-identity` 根目錄操作；倉庫中對應 `examples/js2py/s01-identity`。確認本機可調用 PostgreSQL 18.6 的 postgres、initdb、pg_ctl；本輪位於 /opt/homebrew/bin。不要用已有服務作為替代。

```bash
export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
export UV_PYTHON_INSTALL_DIR=/tmp/langshift-js2py-python-20260928
export UV_CACHE_DIR=/tmp/langshift-js2py-uv-cache-20260928
unset VIRTUAL_ENV UV_PROJECT_ENVIRONMENT UV_ACTIVE UV_PYTHON UV_CONFIG_FILE
export UV_NO_CONFIG=true
uv --version
uv sync --locked
uv run --locked python --version
uv run --locked python labdb.py start
```

預期 uv 0.12.13、Python 3.13.15。labdb.py 創建模式 0700 的 mkdtemp 目錄、模式 0600 的歸屬標記與 .lab-state.json，啟動無 TCP 監聽的 PG。**將它打印的 DATABASE_URL export 行復制到本終端**；該 URL 是私有 socket 地址，不含密碼。isolation.py 在連接前刪除所有隱式 PG* 配置，子命令也排除 PGHOSTADDR/PGSERVICE 等 libpq 環境干擾。別把任意已有 DATABASE_URL 繼續帶入實驗。然後執行：

```bash
uv run --locked alembic upgrade head
uv run --locked alembic current
uv run --locked python admin.py create-user Alice
uv run --locked python serve.py --port 8061
```

current 必須為 004_identity。舊 D 用戶經 004 遷移後保持停用、沒有默認密碼，需明確開通。create-user 拒絕覆蓋已經設置的密碼。新密碼 15–128 字符，只在 getpass 提示中輸入並確認，不放在參數、日誌、環境默認值或教程常量裡。禁止盲目 stamp；安全 downgrade 故意不自動刪除歷史。

/health/live 只檢查進程；/health/ready 檢查 DB 可用及精確遷移版本，不檢查所有數據不變量。另開終端進入同目錄，客戶端不需要 DATABASE_URL。HTTP 端口若衝突，保留已有進程，停止自己啟動失敗的命令或換一個空閒端口，並在所有客戶端命令中同步替換；不要按進程名批量 kill。

## 4. 身份、API 與字段契約

所有包都提供 POST /auth/token、GET /users/me、POST /users/me/password、POST /auth/logout 與 /auth/logout-all。密碼是 JSON 請求體裡的秘密，但只通過客戶端專用提示命令輸入。登錄返回的隨機 Bearer 只在客戶端私有 .session*.json 保存，模式 0600；不 cat、不截圖、不提交。客戶端用 `ProxyHandler({})` 顯式禁用環境代理、拒絕重定向，登錄響應設 no-store；只寫迴環 URL 並不能繞開繼承的代理。這個終端文件不是瀏覽器 localStorage 建議。

Argon2id 由成熟 argon2-cffi 實現，隨機鹽、m=65536 KiB/t=3/p=4；令牌由 secrets.token_urlsafe(32) 生成，DB 僅存 SHA-256 摘要、expiry、auth_version。普通請求重新查啟用/撤銷/過期/版本，不能只看登錄時成功。改密與 logout-all 提升版本；disable/enable 均提升版本，所以舊令牌不會復活。用戶共享鎖與撤權排他鎖定義順序：既有操作可以完成，撤權提交後的新操作被拒絕，不追回已開始響應。

## 5. 真實客戶端驗收

```bash
uv run --locked python client.py --port 8061 --session .session-alice.json login Alice
uv run --locked python client.py --port 8061 --session .session-alice.json request GET /users/me
cp -p .session-alice.json .session-before-change.json
uv run --locked python client.py --port 8061 --session .session-alice.json change-password
uv run --locked python client.py --port 8061 --session .session-before-change.json request GET /users/me
```

```bash
uv run --locked python client.py --port 8061 --session .session-alice.json login Alice
uv run --locked python client.py --port 8061 --session .session-alice.json request POST /auth/logout-all
uv run --locked python client.py --port 8061 --session .session-alice.json request GET /users/me
```

預期：登錄200→me200→改密204/空正文→舊副本401；新密碼登錄200→logout-all204→舊令牌401。改密客戶端刪除當前私有文件，真正失效來自數據庫版本而不是刪除文件。另用兩個文件分別登錄，單會話 logout 後另一會話仍有效；disable 後登錄/舊會話均401，enable 後舊會話仍401，再登錄才200。錯誤賬號與錯誤密碼使用相同401；格式錯誤為脫敏422。不要把憑證值寫入驗收記錄。

## 6. 自動驗收與失敗恢復

```bash
uv run --locked python -m pytest -q
```

當前 22 個用例。fixture 忽略外部 DATABASE_URL，為自己創建 PG18.6、遷移、啟動真實 Uvicorn，標準庫客戶端發實際 HTTP；每例僅清理自己庫中的聲明表。它運行 solutions 擴展入口並複驗基礎路由，覆蓋獨立變式。輸出案例數和脫敏證據見 VERIFICATION.md。維護者設置 SECURITY_EVIDENCE_DIR 可保存脫敏 HTTP/兩連接觀察；這不是生產審計日誌。

| 失敗 | 觀察與恢復 |
| --- | --- |
| 缺/錯 DATABASE_URL | 不輸出實際連接字符串；重新複製本實驗 labdb.py status 的 export |
| ready503、live200 | 核查自有PG狀態和遷移版本；修復後ready200，不跳過遷移 |
| 錯誤/過期/篡改Bearer | 通用401；用專用客戶端重新登錄，不改數據庫繞過驗證 |
| 密碼/JSON/extra字段不合法 | 422僅loc/type，不回顯input/ctx/msg或秘密字段名；修正輸入 |
| 真實數據庫操作錯誤 | 泛化409或503；事務回滾，恢復schema後後續請求成功；不輸出SQL驅動細節 |
| 臨時服務端口被佔 | 不殺已有進程；只更改自己的服務/客戶端端口 |

測試真的令會話過期、破壞Bearer字符、停用/啟用、改密、重啟API及自有PG，並檢查敏感字段、額外鍵、破損JSON的輸出與應用/PG日誌。S02/S03還檢查body/query/path輸入；併發撤權有不同backend PID和pg_blocking_pids證據。它不證明每個未知異常、第三方日誌、代理或APM都已脫敏；未來新增路徑需獨立安全審查。

客戶端隔離迴歸僅用自有迴環監聽器和合成憑證：代理環境有值、no_proxy不存在，目標收到3個請求、代理0個、重定向目標0個。另一helper測試注入無效PGHOSTADDR/PGSERVICE/PGUSER/PGDATABASE/PGPASSWORD後，仍成功啟動、重啟並刪除自己的socket-only集群。

維護者從乾淨副本復跑時，倉庫runner支持 `--lab-root /path/to/extracted-lab` 或 `JS2PY_LAB_ROOT`（也可指定包含同名實驗目錄的父目錄）。它清除繼承的VIRTUAL_ENV、UV_PROJECT_ENVIRONMENT、UV_ACTIVE、UV_PYTHON及其餘UV配置重定向，設置UV_NO_CONFIG、命令行固定Python，只保留明確UV_PYTHON_INSTALL_DIR/UV_CACHE_DIR存儲路徑；還排除PG*及pytest插件/參數覆蓋。默認源碼復跑也只使用該實驗自己的.venv，並拒絕環境符號鏈接。

## 7. 獨立重建與變式
只帶環境/遷移到新目錄，不導入參考app，重寫模型、密碼服務、會話查驗/撤銷和受控賬號命令。用錯誤、過期、篡改、改密、禁用、兩種撤銷、真實重啟和脫敏驗收。變式增加當前有效會話數量：兩登錄=2、撤一個=1、全部撤銷後新登錄=1；不計Bob/舊版本/過期/已撤記錄，也不返回摘要。先獨立實現，後看 solutions/session_count.py。
```bash
uv run --locked python serve.py --port 8061 --app solutions.session_count:app
uv run --locked python client.py --port 8061 --session .session-alice.json request GET /users/me/session-count
```

## 8. 暫停、恢復與最終清理

先在擁有API的終端Ctrl-C。保留數據時運行labdb.py status，保存不含秘密的狀態記錄，下次複製它打印的export，再啟動API。需要證明數據庫持久化時用restart；不要用stop後數據消失來聲稱持久化失敗。

```bash
uv run --locked python labdb.py status
uv run --locked python labdb.py restart
```

API重啟/PG重啟後，仍在有效期且未撤銷的會話/已提交記錄應保留。會話仍可能因正常TTL到期而401；這不是丟庫。完整結束時，先停API，再執行：

```bash
uv run --locked python labdb.py stop
```

**stop確認歸屬和進程退出後會刪除整個臨時PG數據目錄。** 只清理自己創建的私有.session文件，不用全盤通配符，不殺用戶DB。

```text
checkpoint: s01-identity
migration: 004_identity
last_result: record status and non-secret object IDs only
credential_values: never recorded
api: stopped in owning terminal
postgres: retained for resume OR explicitly deleted by owned helper
next: status, export, migrate if needed, serve, fresh login if expired
```

## 9. 打包與未驗證邊界

同級 `s01-identity-files.json` 是正向allowlist；打包只讀取其中路徑，不遞歸整個實驗目錄。排除 .venv、__pycache__、.pytest_cache、.env*、.lab-state.json、.session*（含中斷留下的.new）、PGdata/socket、日誌、憑證和臨時證據。文件列表由集成方打包；本包不捆綁運行環境或數據庫。

未驗證：生產TLS、限流/容量、請求體大小、洩露密碼篩查、找回/MFA、外部日誌/APM、任意未知異常、時鐘偏差、備份恢復、RLS、跨服務副作用和所有鎖交錯。全局列表/已開始響應不能追溯撤權；邀請目標併發被禁用不構成原子開通保證。S03也不承諾清理後永久去重、恰好一次或無條件自動重試。測試通過不等於安全審計通過，主線將按最終文件hash獨立審查。
