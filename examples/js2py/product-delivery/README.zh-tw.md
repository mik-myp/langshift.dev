# 產品交付模板

這些文件是把 V4 產品接入真實目標環境的中立模板。它們不是已部署應用，也不能替代學習者自己的 S03 授權、數據庫模型、遷移或 O04—O06 運維證據。

## 使用順序

1. 先把空白的 `starter/` 目錄複製為自己的產品倉庫；之後再把審查過的運維文件複製到 `ops/` 與 `.github/workflows/`。
2. 替換 `app`、`migrations`、健康路由、鏡像、域名、服務賬戶、數據庫服務名和秘密引用。
3. 按官方文檔核對目標 Docker Engine、Linux/systemd、Caddy、PostgreSQL、CI 和秘密存儲版本。
4. 在一次性 PostgreSQL 服務上運行驗證作業。
5. 在獲批目標中執行審查過的遷移，啟動應用，驗證真實 HTTPS，並運行已認證/越權冒煙場景。
6. 受邀使用前演練備份、隔離恢復、應用回退和會話/成員失效。

文件不包含憑證。`product.service.template` 是 Compose 路徑之外的 systemd 替代方案；同一目標只選擇一種進程監督方式。`commands/release.sh` 在缺少不可變 app/Caddy 摘要、V0—V3 全部通過的格式有效整合記錄、已通過的構建、遷移、備份恢復和回退證據、人工批准、備份政策或回退責任人時會拒絕執行。它也不會因此認證後端或公網運營。`commands/restore.sh` 只接受全新的 `restore_` 數據庫名，不提供覆蓋或 `--clean` 回退。

CI 的 `release` 作業會故意失敗，直到學習者實現並審查 `ops/deploy-approved.sh`。驗證作業變綠不是部署批准。備份和恢復腳本要求審查過的 `pg_service.conf` 與受保護 passfile；不要把密碼寫進服務文件、命令參數或倉庫變量。

## 文件說明

- `starter/`：故意空白的 V0 產品目錄，不包含實現和鎖文件。
- `Dockerfile`、`.dockerignore`、`compose.production.yaml`：鏡像、構建上下文、網絡、秘密、卷和進程邊界。
- `Caddyfile.template`：同主機/容器反向代理起點。
- `product.service.template`：Linux/systemd 替代入口。
- `.github/workflows/verify-and-release.yml.template`：一次性 CI 數據庫、鎖定驗證、環境審批和顯式部署適配門檻。
- `commands/release.sh`：目標發布骨架。
- `commands/backup.sh`、`commands/restore.sh`、`pg_service.conf.template`：受控備份與隔離恢復骨架。
- `app/secret_config.py`、`app/healthcheck.py`：必須接入學習者真實應用的應用適配器。
- `product-workbook.zh-tw.md`：把章節實驗轉成自己產品的分階段工作包。


這裏使用的官方機制包括 [uv Docker 集成](https://docs.astral.sh/uv/guides/integration/docker/)、[Docker 構建最佳實踐](https://docs.docker.com/build/building/best-practices/)、[Caddy 自動 HTTPS](https://caddyserver.com/docs/automatic-https)、[GitHub Actions 環境](https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments)和 [PostgreSQL pg_restore](https://www.postgresql.org/docs/18/app-pgrestore.html)。
## 貫穿整合證據記錄

`templates/integration-record.json` 用讀者聲明的方式記錄 V0—V5。複製到自己的產品倉庫，替換佔位產品身份，並隨進度更新階段與證據狀態。

在解壓後的目錄運行格式檢查器：

```bash
python3 check_integration_record.py templates/integration-record.json
```

檢查器只驗證欄位形狀、階段/證據一致性、相對 artifact 引用、UTC 時間戳和明顯的嵌入憑證。它不會打開引用文件、執行測試、檢查後端、證明脫敏、授予畢業或批准公網運營。通過格式檢查的記錄仍需 artifact 與人工審查。
- `templates/product-contract.md`：V0 產品合同模板。
- `templates/integration-record.json`：V0—V5 證據聲明；檢查器只驗證格式。
- `templates/incident-record.template`：事故與修復記錄。
- `templates/maintenance-record.template`：可復用維護證據記錄。
- `check_integration_record.py`：格式檢查器；不執行產品，也不批准發布。
