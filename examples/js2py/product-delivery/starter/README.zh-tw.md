# 學習者產品啟動包

這是 js2py 貫穿產品的故意空白 V0 啟動包。它沒有業務實現、參考答案、鎖文件，也不聲稱測試通過。

## 開始

```bash
uv python install 3.13.15
uv lock
uv sync --locked
```

此時 `pytest` 不會發現測試；這不是驗收。繼續寫自己的產品合同和第一批業務規則。

## 必須由學習者創建的文件

自己創建這些文件：

- `docs/product-contract.md`
- `docs/integration-record.json`
- 自己的 `src/product/` 模組
- 業務與失敗測試
- 之後：API 入口
- 之後：遷移與數據庫測試
- 之後：發布與恢復運行入口

從交付包中把 `templates/product-contract.md` 複製為 `docs/product-contract.md` 並填寫；把 `templates/integration-record.json` 複製為 `docs/integration-record.json`。兩者都要提交；它們是產品文檔，不是生成緩存。

生成的 `uv.lock` 屬於你自己的產品。不要複製章節實驗的鎖文件或已安裝環境；每次有意變更依賴時再更新它。

## 邊界

這個啟動包只固定初始責任佈局，不實現任務、API、PostgreSQL、授權、異步、部署或恢復；這些都是學習者 V0—V5 的工作。
