# u12-models

本地實驗，2026-09-28 實測 CPython 3.13.15、uv 0.12.13、pytest 8.4.2。業務運行只使用標準庫。

解壓下載包並進入 `u12-models`。不要複製 `.venv`，用聲明與鎖恢復環境。

```bash
uv sync --locked
uv run --locked python app.py
uv run --locked python -m pytest -q
uv run --locked python -m pytest -q solutions/test_work_log.py
```

默認套件 9 項，獨立參考變式 2 項。先按教材需求自己實現，再看 `solutions`；默認發現範圍不含 `errors` 中的刻意失敗。

shared_state 無異常卻共享列表；missing_self 拋 TypeError；no_validation 證明 RawEstimate 不執行字段校驗。公開屬性仍能繞過初始化規則。

完整教材說明預期輸出、逐條失敗命令、機制、獨立需求與邊界。本包是網頁展示的源碼來源，不含環境與憑證。暫停記錄源碼改動、解釋器版本、工作目錄、最後成功命令、未解決失敗和下一步。通過本地實驗不等於能直接交付後端。
