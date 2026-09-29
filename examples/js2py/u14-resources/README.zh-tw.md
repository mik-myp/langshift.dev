# u14-resources

本地實驗，2026-09-28 實測 CPython 3.13.15、uv 0.12.13、pytest 8.4.2。業務運行只使用標準庫。

解壓下載包並進入 `u14-resources`。不要複製 `.venv`，用聲明與鎖恢復環境。

```bash
uv sync --locked
uv run --locked python app.py
uv run --locked python -m pytest -q
uv run --locked python -m pytest -q solutions/test_new_report.py
```

默認套件 12 項，獨立參考變式 2 項。先按教材需求自己實現，再看 `solutions`；默認發現範圍不含 `errors` 中的刻意失敗。

two_yields 在退出時失敗；suppressed 有意吞異常，是反例。break 不保證關閉。new_report 失敗會留部分內容；關閉不是回滾、持久化或抗崩潰保證。

完整教材說明預期輸出、逐條失敗命令、機制、獨立需求與邊界。本包是網頁展示的源碼來源，不含環境與憑證。暫停記錄源碼改動、解釋器版本、工作目錄、最後成功命令、未解決失敗和下一步。通過本地實驗不等於能直接交付後端。
