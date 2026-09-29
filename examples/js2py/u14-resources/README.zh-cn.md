# u14-resources

本地实验，2026-09-28 实测 CPython 3.13.15、uv 0.12.13、pytest 8.4.2。业务运行只使用标准库。

解压下载包并进入 `u14-resources`。不要复制 `.venv`，用声明与锁恢复环境。

```bash
uv sync --locked
uv run --locked python app.py
uv run --locked python -m pytest -q
uv run --locked python -m pytest -q solutions/test_new_report.py
```

默认套件 12 项，独立参考变式 2 项。先按教材需求自己实现，再看 `solutions`；默认发现范围不含 `errors` 中的刻意失败。

two_yields 在退出时失败；suppressed 有意吞异常，是反例。break 不保证关闭。new_report 失败会留部分内容；关闭不是回滚、持久化或抗崩溃保证。

完整教材说明预期输出、逐条失败命令、机制、独立需求与边界。本包是网页展示的源码来源，不含环境与凭证。暂停记录源码改动、解释器版本、工作目录、最后成功命令、未解决失败和下一步。通过本地实验不等于能直接交付后端。
