# 恢復驗收與受控開放 — o06-recovery

完整獨立本地實驗。先讀 O04/O05/O06 對應正文，不導入其他章節目錄。
旁邊 `o06-recovery-files.json` 是網頁與下載的明確 allowlist，不能遞歸壓縮當前工作目錄。

## 實測環境與命令

日期 2026-09-28。CPython3.13.15、uv0.12.13、pytest8.4.2、FastAPI0.135.1、
Uvicorn0.42.0、Pydantic2.12.5、HTTPX0.28.1、SQLAlchemy2.0.54、Alembic1.20.0、
psycopg[binary]3.3.6、PostgreSQL18.6、Argon2-cffi25.1.0。Starlette0.52.1、
AnyIO4.12.1 固定兼容；requires-python 為 >=3.13,<3.14，uv package=false。
真實鎖來自 public PyPI，包含製品哈希。

在解壓目錄運行。postgres/initdb/pg_ctl/psql/pg_dump/pg_restore 必須事先存在於
/opt/homebrew/bin 或指定 PG_BIN 目錄。本實驗不安裝系統服務器；錯誤版本會在
修改數據庫前拒絕。其他操作系統需另行運行驗證，不用 macOS 結果冒充 Linux。

倉庫總 runner 為子進程重建環境：丟棄繼承的 `UV_*`、虛擬環境選擇與 Python 注入設置，再固定課程 cache/Python 安裝目錄、public PyPI 和 `UV_NO_CONFIG=1`；`PG*` 也只保留 `PG_BIN`。實測使用自己創建的“外部虛擬環境”誘餌、錯誤解釋器路徑和無效用戶 uv 配置，確認安裝只發生在當前乾淨副本的 `.venv`，誘餌目錄內容不變。不要把這些防護誤解為能修復已經在腳本啟動前運行的外層 uv：手動執行下方 uv 命令前，應退出其他虛擬環境並使用乾淨終端；清除 `VIRTUAL_ENV`、`UV_PROJECT_ENVIRONMENT`、`UV_ACTIVE`、`UV_PYTHON`、`UV_CONFIG_FILE` 等覆蓋項，並設置 `UV_NO_CONFIG=1`。若直接 Python 入口拒絕 PG 變量，只在本次實驗環境中移除它報告的名字，不修改生產配置、更不打印其值。

```bash
uv sync --locked
uv run --locked python ci.py
uv run --locked python -m pytest -q solutions
uv run --locked python demo.py
```

ci.py 檢查語法、運行 6 項正常測試與真實進程/數據庫演練；獨立答案另有
1 項測試。ci.py 已包含 demo，單獨 demo 用全新集群重放。穩定 PASS 行
代表已檢查階段；耗時是測量值而非固定輸出。語法、mock 決策、檢查 YAML 都不
代替實際運行。

## 本章實際證明的內容

其中三項恢復專項使用真實 PostgreSQL，分別驗證實際導入、損壞拒絕與目標不可覆蓋。演練生成 custom pg_dump，
檢查目錄與哈希，恢復到全新隔離庫，比較全部表內容指紋，再測約束、identity
序列和運行角色權限。截斷副本既被校驗和拒絕，也實際觸發 pg_restore 失敗；
壞目標沒有用戶表。只有 .dump 文件或能列目錄絕不算恢復通過。

快照可能復活已撤銷 token 或舊成員關係。開放運行角色 CONNECT 之前，先停用
恢復賬戶、遞增 auth_version、刪除會話，再核對合成的備份後安全變更記錄，
僅明確批准測試賬戶。真實 HTTP 驗證舊/過期 token 和跨用戶讀取被拒絕。
真實環境缺少權威較新安全記錄時保持賬戶停用、目標隔離，不能把舊備份當現狀。

源庫保留一條刻意在快照後提交、恢復庫沒有的任務。MEASURED 僅報告本次快照
年齡與恢復加驗收耗時，不是生產 RPO/RTO。pg_dump 不自動覆蓋角色/全局對象、
配置/密鑰/外部文件。源與目標在同一自有宿主；未驗證跨機容災、定時/加密/
異地保留或 PITR。合成歸檔放在 0700 目錄下、模式 0600，退出刪除。
獨立清單門禁不能替代真實恢復。

## 環境邊界與端口所有權

傳入私有 socket 的 host 還不夠：libpq 仍可能從 `PGHOSTADDR`、`PGSERVICE`、`PGSERVICEFILE` 等環境變量取得另一個連接默認值。`reject_connection_environment` 在創建臨時目錄之前，以及每次直接連接、遷移和服務啟動之前，拒絕繼承的全部 `PG*` 變量，唯一例外是隻定位可執行文件的 `PG_BIN`。錯誤只列變量名，不打印值，也不修改調用者環境。Python 連接、SQLAlchemy 的連接創建器和 PG 子命令都使用自有目錄內的空白 0600 `empty.pgpass`，不讀取用戶的默認密碼文件。直接運行 `demo.py` 或 `ci.py` 也執行這些防護，不依賴倉庫總 runner 先替它清理。

啟動 API 不再先探測空閒端口、關閉探測 socket，再要求另一個進程搶佔同一號碼。Uvicorn 自己用 `--port 0` 完成綁定；控制器從**該子進程自己的私有啟動日誌**讀取實際端口，再請求 readiness。`--no-access-log` 不關閉 info 級啟動 banner；控制器固定無顏色日誌和單 worker。兩個同版本服務也使用不同日誌文件。測試實際同時啟動兩個服務，核對兩個不同端口、各自 banner、真實請求和退出清理。這消除了選端口後釋放再綁定的窗口，不是對任意併發故障的保證；未來 Uvicorn 改變 banner 格式時會超時拒絕，不猜測端口。

`tests/test_environment.py` 提供 3 項補充驗收：繼承 PG 默認值在分配/連接前被拒絕，`PG_BIN` 與自有空密碼文件保持明確邊界，以及兩個真實服務各自綁定端口 0、通過 HTTP 後完整退出。PG 變量矩陣是一項測試裡的多組斷言，不誇大成多項 pytest 用例。

## 安全、身份與完整源碼

ops/cluster.py 只創建自己的 mkdtemp /tmp/ls-ops-* 集群；停止/刪除前核對 UID、
0700、所有權隨機標記與 symlink，不接受環境裡的 DATABASE_URL，不管理用戶
已有 PostgreSQL。數據庫只使用私有 0700 Unix socket 的本地 trust，不監聽 TCP；
這是短命教學政策，不是生產認證。同一個操作系統賬戶仍然是信任邊界。
API 只綁定 127.0.0.1 的自有臨時端口。

ops/app.py 是受保護項目的運維切片，不是完整 capstone。保留 D/S status/
description/priority 字段，不沿用 H done/note；每請求檢查 opaque Bearer
摘要/expiry/revoked/active/auth_version，無權限的項目 404。操作員 fixture
建立合成用戶、會話和非空冪等回執，不提供公開登錄/開戶後門；真實上線前仍需
整合完整 S03 應用。

SQL001..006 獨立復現 D/S 合同快照，007 添加可空 projects.description。
它們只用於自有實驗，不允許替換既有生產遷移歷史。應用啟動只做兼容檢查，
絕不自動遷移。管理遷移與運行身份分離，grants.sql 列出當前實驗權限，不代表已經最小授權。
遷移控制器按單操作員串行執行，不是分佈式發佈鎖。

本實驗驗證的是管理／運行身份分離，以及已測試的 ALTER/DROP 被拒絕；**沒有證明 DML 已按最小權限收斂**。共用的 `sql/grants.sql` 仍對 projects、project_members、tasks 授予 SELECT/INSERT/UPDATE/DELETE，並對 public 的全部序列授予 USAGE/SELECT；其中部分權限超過當前「讀取／創建項目」路由的需要。真正部署前，須逐個列出路由和作業需要的表操作，收窄表／序列授權，再驗證必要操作成功、未使用的 UPDATE/DELETE 等操作被拒絕。已有 DDL 拒絕測試不能代替這項審計。

ops/server.py 管理實際 Uvicorn 子進程，等待 DB-backed readiness，在 finally
只停自己的服務。正常/異常退出清理自有庫目錄、合成歸檔、私有日誌和 socket；
若停止/所有權檢查失敗，寧可拒絕刪除也不觸碰別人的服務。異常中斷後僅排查
本次擁有的根目錄；不使用全局 killall、外部 URL 的 DROP、Docker prune 或
寬泛遞歸刪除。這裡不應出現真實憑證或真實用戶數據。

## 故障與恢復

工具缺失/版本錯誤：修工具路徑，不繞過檢查。所有權拒絕：重開新實驗，不把
用戶目錄偽裝成實驗。刻意的遷移/權限/損壞失敗有斷言和修復複驗；意外非零
退出就停止門禁，不能忽略後繼續發佈。原始異常、URL、環境整表可能含秘密，
不要為診斷全量打印。

暫停記錄工作目錄、鎖哈希/版本、最後階段、真實用例數、刻意/意外故障、兼容/
恢復狀態、私有日誌/歸檔政策、進程目錄清理、未驗證外部門檻、下次動作。
正常退出會刪臨時狀態，恢復時重新運行，不假定舊 socket/token 文件還在。

## 明確 pending 的外部驗收

本機實跑只有 macOS arm64、PG18.6 與 loopback HTTP。沒有實際 Linux/systemd、
Docker build/run、Caddy/公網代理、域名/DNS/公網 TLS、託管 CI、鏡像發佈、
生產遷移/切流、告警送達、定時加密/異地備份、跨機恢復、代表性壓測或受邀用戶
試用。這些需要獨立環境與授權。不能把 YAML 當發佈，把告警返回值當通知送達，
把備份文件當恢復成功。

完整 S03 認證授權、請求體邊界、密碼哈希容量、登錄限流、可信代理/CORS/憑證
策略及 O01-O03 外部門檻仍是上線前提；不擴成公開註冊。本實驗不做 Git 提交/
推送、不購買基礎設施、不執行真實部署。

## 打包與來源

只包含 allowlist 源碼、SQL、配置、鎖和文檔。排除 .venv、__pycache__、
.pytest_cache、.env/.env.*、憑證、日誌、歸檔、PG數據/socket、運行時清單。
SOURCES.md 是 2026-09-28 實時核驗的一手資料。倉庫可選維護腳本
scripts/test-js2py-operations-delivery.py 檢查干淨清單副本與真實演練，不替代
缺失的外部發布門檻。
