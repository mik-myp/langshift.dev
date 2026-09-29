# L08 — Environments and dependencies / 环境与依赖 / 環境與依賴

Verified baseline: CPython 3.13.15, uv 0.12.13, humanize 4.13.0, 2026-09-28.
This is a tested baseline, not a latest-version or long-term security claim.

## Start / 开始 / 開始

Extract the complete ZIP. Open its `u08-environments` directory in a terminal.
Run these commands there, without adding `--no-project`:

```sh
uv --version
uv sync --locked
uv run --locked python probe.py
uv run --locked python app.py
```

`app.py` prints `Files: 3`, `Bytes: 1536`, and `Readable: 1.5 KiB`.
Paths in the probe depend on where you extracted the download.

解压完整目录，在 `u08-environments` 内执行上述命令，不再加 `--no-project`。
`.python-version` 选择解释器，`pyproject.toml` 声明兼容范围与直接依赖，
`uv.lock` 记录解析结果；`.venv` 是可以重建的本地安装，不是源码或备份。
第一次同步可能联网下载 Python 或包。离线且未缓存的机器不能凭锁文件生成包内容。
锁文件不是安全审计，不保证所有平台和系统库都能重现。

解壓完整目錄，在 `u08-environments` 內執行上述命令，不再加 `--no-project`。
`.python-version` 選擇解釋器，`pyproject.toml` 聲明相容範圍與直接依賴，
`uv.lock` 記錄解析結果；`.venv` 是可重建的本地安裝，不是原始碼或備份。
第一次同步可能連線下載 Python 或套件。離線且未快取的機器不能憑鎖定檔生成套件內容。
鎖定檔不是安全審計，不保證所有平台與系統函式庫都能重現。

## Deliberate failures / 预期失败 / 預期失敗

- `uv run --locked python errors/show_shadow.py`: AttributeError because
  `errors/humanize.py` shadows the installed package. Rename that local source
  **in a disposable copy**, not the real installed package, then rerun.
- In `exercises/missing-declaration`, run `uv sync --locked`, then
  `uv run --locked python app.py`: ModuleNotFoundError. Repair with
  `uv add "humanize==4.13.0"`, inspect BOTH project declaration and lock, then rerun.
- Change the root dependency to `humanize==4.12.0` in a disposable copy and run
  with `--locked`: stale-lock rejection, not a Python traceback. Restore the
  original declaration to reproduce this download; use an intentional lock update
  only when a dependency change is wanted.

这些失败不应通过忽略错误、全局安装或手改锁文件来“修复”。
這些失敗不應透過忽略錯誤、全域安裝或手改鎖定檔來「修復」。

## Independent transfer / 独立迁移 / 獨立遷移

Create a genuinely empty folder outside the download and implement `report.py`
from the chapter's requirements. The answer in `solutions/size-report` is a
separate non-packaged uv application, not a module imported by the root demo.
Recreate its environment from `.python-version`, `pyproject.toml` and `uv.lock`.
Run `uv sync --locked` and `uv run --locked python report.py` in that folder.
Verify empty input, zero, negative input, bool, numeric strings and changed totals.
Do not copy `.venv`, caches or credentials to another machine.

在下载目录之外独立完成；从声明重建环境，不能靠复制 `.venv` 获得绿色输出。
在下載目錄之外獨立完成；從聲明重建環境，不能靠複製 `.venv` 獲得綠色輸出。

## Maintainer / 维护 / 維護

Three projects use public PyPI lockfiles; no private registry or credentials.
ZIP allowlist excludes `.venv`, caches, experimental edits and generated output.
Rebuild with `python3 scripts/build-js2py-lab.py --lab u08-environments`.
Run the actual integration with `python3 scripts/test-js2py-environments.py`.
