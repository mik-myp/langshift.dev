# O02 容器與可部署應用

前置 O01/L08。這是 health-only smoke app，不含任務、認證、授權或數據庫；不能接真實用戶。Dockerfile/Compose/安全runner 完整提供，但本機沒有容器引擎，真實構建/運行仍待驗收。

## 環境與恢復

核驗日期：**2026-09-28**。需要普通 POSIX 賬戶；不以 root 運行權限實驗。CPython **3.13.15**、uv **0.12.13**、pytest **8.4.2**。`.python-version` 選解釋器，pyproject 聲明 `>=3.13,<3.14`，uv.lock 鎖依賴；`[tool.uv] package=false` 表示不打包這個練習為可發佈 Python 包。

Web 基線：FastAPI **0.135.1**、Uvicorn **0.42.0**、Pydantic **2.12.5**、HTTPX **0.28.1**、Starlette **0.52.1**、AnyIO **4.12.1**；沒有前端依賴。

倉庫用戶從倉庫根目錄執行下列 cd；ZIP 用戶直接進入解壓後的同名實驗根目錄，裡面應有 pyproject.toml。`--locked` 拒絕悄悄更新鎖。

```bash
cd examples/js2py/o02-containers
pwd
uv --version
uv sync --locked
uv run --locked python --version
```

維護者鎖文件已用 `uv lock --default-index https://pypi.org/simple` 實際生成。讀者恢復不需要重新解析。環境與緩存不進清單/ZIP，所有數據實驗用自己創建的臨時目錄。

## 本地可實際執行

local_probe.py 啟動自己持有的 loopback Uvicorn 子進程；目錄不可寫時 live 保持200而 ready變503，恢復後ready200；/tasks404。check_config 只檢查選定不變量，不是 Docker/Compose 完整解析器。secret_demo 僅處理虛構標記且不輸出值。

```bash
uv run --locked python check_config.py
uv run --locked python local_probe.py
uv run --locked python secret_demo.py
uv run --locked python -m pytest -q
uv run --locked python -m pytest -q solutions/test_restore_copy.py
uv run --locked python container_probe.py
```

```text
host_http_live=200
host_http_ready=200
unwritable_live=200
unwritable_ready=503
restored_ready=200
tasks_not_implemented=404
container_runtime=NOT_VERIFIED
```

container_probe 無顯式 opt-in 時 exit77，報告 environment_pending，不能計為容器通過。pytest 標準14、獨立3已實跑。普通文件恢復與真實容器卷驗證是兩個層次。

## 構建與運行邊界

Dockerfile 兩階段恢復鎖定生產依賴，運行用戶10001；.dockerignore先拒絕再明確放行九個文件。compose.json 需顯式 -f，宿主發佈127.0.0.1:8033，容器內部監聽0.0.0.0:8000；兩個網絡命名空間不能混淆。只讀根、/data命名卷、/tmp臨時空間與最小權限分別指定。healthcheck報告就緒，並不會自動完成授權或因unhealthy而重啟。

普通OPS_DATA_DIR不是秘密。密碼/token不得寫入鏡像層、ARG/ENV、命令行、日誌或下載包；secret_demo不是生產秘密管理器。基礎鏡像tag可用性/digest/架構未在引擎實測。卷不是備份；同容器stop/start保留可寫層，刪除重建才不自動保留它。

## 用戶自備受控引擎後的命令（未實跑）

先審讀container_probe.py。需要Linux Docker Engine>=28、本地UNIX socket、鏡像下載許可。不要填遠端TCP/SSH，也不使用默認context。程序清除Docker環境選擇並使用空臨時配置，避免讀取憑證助手；資源名隨機且只移除自己創建的容器/卷/鏡像，不全局prune。基礎鏡像/構建緩存可能保留。實際輸出必須由你的目標環境產生。

```bash
uv run --locked python container_probe.py --socket /path/to/controlled/docker.sock --confirm-controlled-engine
```

runner 驗證 UID、只讀根、host綁定、健康、帶卷重建=1、無卷同實例stop/start=1、無卷重建=0。端口衝突不要kill用戶進程；權限失敗不要把真實數據目錄chmod777。構建失敗應保留階段信息，不能改latest繞開版本約定。

## 獨立需求

把停止寫入的教學counter複製到新空目錄並讀回一致值；拒絕非空目標、拒絕損壞源且不改原狀態。solutions/restore_copy.py和三個測試是參考；不能用普通文件拷貝冒充活躍PostgreSQL備份。

## 環境矩陣（機器可讀版本：ENVIRONMENT.json）

| 狀態 | 證據與門檻 |
| --- | --- |
| 已實際運行 | 配置文件選定不變量、真實loopback HTTP200/503/恢復/404、普通賬戶權限失敗、虛構0600秘密標記、普通文件恢復；沒有顯式許可時runner返回77。 |
| 本機不可運行 | 沒有發現Docker/OrbStack/Podman/Apple container等CLI、常見應用或socket；沒有受控Linux容器引擎。 |
| 用戶需自備 | 受控本地Linux Docker Engine>=28、核實過的UNIX socket、鏡像下載/構建的網絡、存儲和許可；不使用遠端context。 |
| 待環境驗收 | 實際基礎鏡像tag/digest/架構與構建、Compose解析、UID10001/read-only/loopback發佈、卷owner/健康/啟停/刪除重建、引擎runner分支與清理。完整capstone/授權/數據庫另行集成。 |

本輪標準 **14**、獨立 **3** 個測試通過。源碼與文稿 `implemented`；矩陣中的外部環境 `environment_pending`，不是整體部署通過。普通 macOS 測試不能代替 Linux/容器/公網或 Windows 證據。

## 恢復學習與排錯記錄

記錄源碼/鎖摘要、cwd、工具版本、最後成功命令、失敗階段與分類、實際測試數、環境矩陣和下次第一步。不要記錄完整環境、真實 token、數據庫 URL 或私鑰。恢復先 `uv sync --locked`，再跑標準與自己寫的獨立測試。只有參考答案通過，不代表你能獨立實現。

## 一手資料

SOURCES.json 保存 2026-09-28 核驗的官方地址、作用範圍、HTTP獲取結果與SHA-256摘要。章節正文解釋每個機制，README 提供離線運行入口。這裡沒有自動創建生產資源、安裝系統軟件或接受服務條款。
