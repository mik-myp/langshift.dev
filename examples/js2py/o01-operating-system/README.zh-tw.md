# O01 操作系統與服務進程

前置 A02 與語言/文件/依賴/測試基礎。理解程序啟動時的 cwd、環境、權限、端口與退出方式，再討論容器。worker 只保存一次性啟動計數；不是完整任務 API，不是可靠數據庫。

## 環境與恢復

核驗日期：**2026-09-28**。需要普通 POSIX 賬戶；不以 root 運行權限實驗。CPython **3.13.15**、uv **0.12.13**、pytest **8.4.2**。`.python-version` 選解釋器，pyproject 聲明 `>=3.13,<3.14`，uv.lock 鎖依賴；`[tool.uv] package=false` 表示不打包這個練習為可發佈 Python 包。

倉庫用戶從倉庫根目錄執行下列 cd；ZIP 用戶直接進入解壓後的同名實驗根目錄，裡面應有 pyproject.toml。`--locked` 拒絕悄悄更新鎖。

```bash
cd examples/js2py/o01-operating-system
pwd
uv --version
uv sync --locked
uv run --locked python --version
```

維護者鎖文件已用 `uv lock --default-index https://pypi.org/simple` 實際生成。讀者恢復不需要重新解析。環境與緩存不進清單/ZIP，所有數據實驗用自己創建的臨時目錄。

## 文件與實際命令

worker.py 是前臺單寫者，--once 只執行一次。process_lab.py 持有自己創建的子進程並驗證信號；environment_lab.py 明確兩個 cwd 與子進程配置；permissions_lab.py 只改臨時文件；port_lab.py 只創建 loopback sockets。所有運行都有限超時/清理，不搜索或停止別人的進程。

```bash
uv run --locked python process_lab.py
uv run --locked python environment_lab.py
uv run --locked python permissions_lab.py
uv run --locked python port_lab.py
uv run --locked python -m pytest -q
uv run --locked python -m solutions.two_directories
uv run --locked python -m pytest -q solutions/test_two_directories.py
```

關鍵實測輸出如下。負的 -9 是 POSIX subprocess 表示，不是 HTTP 狀態或 shell 必然返回值。

```text
missing_config_exit=78
SIGTERM: subprocess_returncode=0 cleanup=True
SIGINT: subprocess_returncode=0 cleanup=True
SIGKILL: subprocess_returncode=-9 cleanup=False
same_directory_across_processes=2
[2, 1]
```

## 故意失敗與恢復

缺少/相對 OPS_DATA_DIR →78；損壞 JSON、列表根或 bool starts →65；自有不可寫目錄 →74；錯誤 cwd →FileNotFoundError；第二次綁定同一地址被拒絕；SIGKILL 不執行清理。測試確認這些失敗，不把它們轉成業務成功。不要用 sudo/chmod777 掩蓋權限問題。重建新的自有臨時目錄是本實驗恢復，不代表真實數據庫可丟棄。

## 手工 worker 與停止

若要手工運行，先準備只用於本實驗的目錄，通過 OPS_DATA_DIR 傳入絕對路徑，啟動 worker.py；ready 後它一直等待，終端的 Ctrl+C 請求 SIGINT 正常結束。自動腳本負責清理自己的 Popen 對象，完成後不額外 kill。沒有信號/超時證據前不聲稱所有 finally 都會執行。

## Linux/systemd（未實跑）

完整單元在 systemd/ops-worker.service。目標管理員須先確認沒有同名服務或賬戶，在可重建 Linux 主機創建專用 langshift-ops 非登錄賬戶/組，將源碼部署到 /opt/langshift/o01-operating-system 並在目標目錄恢復 .venv；服務賬戶能讀/執行源碼，不能修改它。StateDirectory 負責 /var/lib/langshift-ops。不要複製 macOS .venv，不用生產機器練習。先審核/驗證單元，再經批准安裝到 /etc/systemd/system/ops-worker.service；以下只是在準備完成後可執行的驗收命令，不是成功記錄。

```bash
systemd-analyze verify systemd/ops-worker.service
sudo systemctl daemon-reload
sudo systemctl start ops-worker.service
sudo systemctl status ops-worker.service --no-pager
sudo journalctl -u ops-worker.service -n 30 --no-pager
sudo systemctl stop ops-worker.service
```

## 獨立需求

只根據需求實現：兩個目錄 first/second，給 first 啟動兩次、second 一次，所有子進程 cwd 故意為 second，結果 [2,1]；獨立狀態不靠父進程內存共享。失敗也必須只清理自己資源。參考 solutions/two_directories.py 與單獨測試；先做再看答案。SIGTERM/SIGKILL 的差異、權限恢復、Linux待驗證均應能口頭解釋。

## 環境矩陣（機器可讀版本：ENVIRONMENT.json）

| 狀態 | 證據與門檻 |
| --- | --- |
| 已實際運行 | 普通 macOS 用戶；環境/cwd、缺失文件、SIGTERM/SIGINT清理與SIGKILL不清理、權限拒絕/恢復、loopback端口衝突、配置78/數據65/I-O74、兩份獨立狀態目錄。 |
| 本機不可運行 | 沒有Linux/systemd；沒有創建真實服務賬戶或安裝系統單元。 |
| 用戶需自備 | 可重建受控Linux/systemd主機、專用賬戶/組、經審核部署目錄，以及安裝單元的管理員授權。 |
| 待環境驗收 | 目標機systemd配置驗證、實際啟停/失敗重啟/權限限制；啟用開機啟動前另做生命週期測試。Windows、併發寫與斷電持久性不在通過範圍。 |

本輪標準 **16**、獨立 **1** 個測試通過。源碼與文稿 `implemented`；矩陣中的外部環境 `environment_pending`，不是整體部署通過。普通 macOS 測試不能代替 Linux/容器/公網或 Windows 證據。

## 恢復學習與排錯記錄

記錄源碼/鎖摘要、cwd、工具版本、最後成功命令、失敗階段與分類、實際測試數、環境矩陣和下次第一步。不要記錄完整環境、真實 token、數據庫 URL 或私鑰。恢復先 `uv sync --locked`，再跑標準與自己寫的獨立測試。只有參考答案通過，不代表你能獨立實現。

## 一手資料

SOURCES.json 保存 2026-09-28 核驗的官方地址、作用範圍、HTTP獲取結果與SHA-256摘要。章節正文解釋每個機制，README 提供離線運行入口。這裡沒有自動創建生產資源、安裝系統軟件或接受服務條款。
