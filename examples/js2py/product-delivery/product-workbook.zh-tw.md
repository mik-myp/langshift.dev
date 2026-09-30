# js2py 產品工作包：把章節實驗變成自己的服務

這不是實現答案，也不是按周推進的計劃。你按能力階段工作；可以暫停、恢復、查官方文檔，但每個階段必須在自己的產品倉庫留下可複核證據。

先把 `templates/integration-record.json` 複製到自己的倉庫。每完成一項證據，更新對應狀態；中斷時更新 `next_action` 和產品提交。格式檢查器只檢查記錄形狀，不執行產品。

## V0：自己的 Python 產品基礎

進入條件：已完成 L10，並能在第二個空目錄恢復本地程序。

先複製本交付包中的空白 `starter/` 目錄。把 `templates/product-contract.md` 和 `templates/integration-record.json` 複製到自己的 `docs/`，再生成自己的 `uv.lock`。

你要自己寫：

- `pyproject.toml` 與 `uv.lock`；
- 業務規則模塊；
- 輸入校驗；
- 文件讀寫邊界；
- 普通業務測試；
- 一頁產品契約：任務字段、合法值、缺失值、重複標題、狀態變化。

不能把 L10 下載包或摺疊答案整體複製為產品。參考答案只在獨立嘗試後用來核對職責。

離開證據：

- `environment_recovery`：第二個空目錄恢復並運行；
- `business_tests`：空集合、零值、非法輸入、重複標題、輸入不變；
- `failure_recovery`：壞 JSON 或編碼錯誤不覆蓋舊數據，修復後重跑。

## V1：把同一業務暴露為 HTTP

進入條件：V0 通過，且能解釋每個路由會改變什麼狀態。

你要自己寫：

- FastAPI 應用入口；
- 請求與響應模型；
- 路由組織；
- 配置讀取；
- TestClient 測試；
- 真實 Uvicorn 請求記錄；
- 最小瀏覽器或 HTTP 客戶端聯調記錄。

內存存儲可以存在，但運行文檔必須寫明重啟丟數據，且不能稱為上線版本。

離開證據：

- `http_contract`：方法、狀態碼、字段、錯誤形狀；
- `api_tests`：成功、422、404、PATCH 三態、輸出過濾；
- `real_process_requests`：真實端口上的請求與清理記錄。

## V2：把狀態放進 PostgreSQL

進入條件：V1 通過，且能解釋內存狀態為什麼不能滿足重啟和併發。

你要自己寫：

- users/projects/project_members/tasks 關係設計；
- SQLAlchemy 模型；
- Alembic 遷移；
- 每請求 Session 與事務邊界；
- 隔離數據庫測試；
- API 存儲替換後的迴歸。

不要用 `create_all` 代替遷移，也不要刪庫重建解決已有數據變化。

離開證據：

- `empty_database_migration`：空庫升級；
- `existing_data_migration`：已有數據升級並核對；
- `transaction_failure_recovery`：兩步寫入第二步失敗後無殘留；
- `isolated_database_tests`：測試庫可重複清理。

## V3：登錄、對象授權與冪等

進入條件：V2 通過，且數據庫與應用版本兼容記錄存在。

你要自己寫：

- 受控開戶命令；
- Argon2id 密碼哈希；
- 不透明 Bearer 會話；
- 會話摘要、過期、撤銷和認證版本；
- 每請求身份重建；
- 項目成員作用域查詢；
- 對象級授權；
- 創建任務冪等回執。

請求體不能自報 `user_id`、角色或創建者。前端隱藏按鈕和 CORS 不是授權。

離開證據：

- `identity_lifecycle`：登錄、改密、停用、退出全部會話；
- `object_authorization_negative`：Alice 知道 Bob ID 也無法讀寫；
- `revocation`：移除成員後舊憑證失去對象權限；
- `idempotency_and_retry`：同 key 同內容重放、異內容衝突、真實競爭。

## V3.5：只在需要處加入異步

進入條件：V3 通過，且有一個真實可選外部依賴需求。

你要自己寫：

- 外部適配器；
- 共享客戶端生命週期；
- 總預算和階段超時；
- 有界併發；
- 響應驗證；
- 取消清理；
- 故障替身測試。

核心 CRUD 不依賴外部服務成功。不要把 `BackgroundTasks` 或內存隊列稱為持久任務系統。

離開證據：

- `external_failure_isolation`：外部失敗不影響任務讀寫；
- `cancellation_cleanup`：取消後無任務或客戶端洩漏；
- `core_crud_regression`：核心 CRUD 迴歸仍通過。

## V4：真實目標環境發佈與維護

進入條件：V3/V3.5 通過，且你已獲准使用目標主機、域名、證書、秘密存儲、數據庫、CI 和通知渠道。

你要自己接入：

- Docker 或 systemd 運行入口；
- 遷移身份與應用身份；
- Caddy 或等價 HTTPS 入口；
- 託管 CI；
- 日誌、關聯 ID 和告警；
- 備份、隔離恢復、回退手冊；
- 受邀試用範圍和維護責任人。

本地 O 階段實驗證明機制，不證明你的產品可上線。

離開證據：

- `build_identity`：固定提交和鏡像摘要或製品標識；
- `controlled_migration`：真實目標遷移命令與版本；
- `public_https`：外部 DNS、證書鏈和真實 HTTPS 請求；
- `logs_and_delivered_alert`：一次故障定位和實際送達通知；
- `backup_and_isolated_restore`：備份、恢復、數據/權限驗證；
- `compatible_rollback`：有數據回退或安全凍結證據；
- `invited_use_approval`：範圍、批准人和維護責任。

## V5：獨立新需求

進入條件：V4 已通過，且你已閱讀 G01 場景目錄。

你要自己完成 G01 的任務評論需求：

- 關係與接口設計；
- 遷移；
- 權限；
- 併發與重複請求；
- 發佈回退；
- 恢復驗證；
- 人工評閱。

離開證據：

- `independent_feature`；
- `feature_release_and_rollback`；
- `feature_restore`；
- `human_review`。

## 暫停與恢復

每次暫停記錄：

- 當前階段；
- 產品提交；
- schema 版本；
- 最後成功命令；
- 實際失敗；
- 已清理的進程；
- 未驗證門檻；
- 下一個具體動作。

恢復時先復現上一次可運行狀態，再繼續。不要因為間斷重裝一切，也不要為了推進而刪除失敗證據。

## 維護證據記錄

每處理依賴/安全更新、證書續期、備份或恢復、事故、權限變更、用戶反饋跟進、容量/成本審查，都使用 `templates/maintenance-record.template` 保存一條記錄。記錄責任人、產品/schema 版本、已核對官方資料、動作、測試、備份恢復證據、通知送達證據、回退兼容性、未解決風險和下次審查觸發條件。
