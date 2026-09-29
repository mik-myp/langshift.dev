# A01 — Python 异步执行模型

核验日期 2026-09-28。这是位于 S03 后的独立本地实验，不是完整 capstone，
不导入其他章节源码。前置为 Python 函数、异常、上下文管理器、测试和已有的
同步 API/SQL/认证基础；A02 另以 A01、L14、H05 为前置。

## 从干净下载复现

解压后进入 `a01-async-model`；仓库中进入 `examples/js2py/a01-async-model`。
固定 CPython 3.13.15、uv 0.12.13、pytest 8.4.2，先安装指定 uv，本实验不替你升级工具。
没有第三方运行时依赖。
Web 框架沿用 H03–H06 基线，生命周期依赖沿用 H05–H06。
真实 public-PyPI lock 含解析结果和制品哈希，requires-python 只接受 3.13，
`tool.uv.package=false` 表示直接运行本地源码，不安装本项目为包。
不要删锁或无声升级框架。

```bash
# Run from the extracted a01-async-model directory.
set -eu
export PATH="$HOME/.local/bin:$PATH"
export UV_PYTHON_INSTALL_DIR=/tmp/langshift-js2py-python-20260928
export UV_CACHE_DIR=/tmp/langshift-js2py-uv-cache-20260928
uv --version
uv python install 3.13.15
uv sync --locked
uv run --locked python --version
uv run --locked python app.py
uv run --locked python -m pytest -q
uv run --locked python -m pytest -q solutions
```

两个 /tmp 目录隔离解释器与下载缓存，不保存业务数据。安装锁定公共依赖需要联网，
实验运行不访问收费/第三方服务、不发送用户数据。

## 稳定演示输出

输出以 `expected-output.txt` 为源，实际运行必须匹配。

```text
creation: called:no-body-yet | A:start | A:end
sequential: A:start | A:end | B:start | B:end
scheduled: A:start | B:start | owner:both-entered | B:end | A:end
blocking: sync:start | sync:end | callback:ran | owner:resumed
offloaded: loop:responsive-while-thread-waits | thread:returned
cancelled: file:opened | file:closed | owner:cancelled
timeout: file:opened | file:closed | owner:timeout
bounded: peak=2 active=0
```

主测试 **19 passed**，独立答案测试 **5 passed**。耗时不是正确性断言。
除故意收集警告的诊断外，警告视为错误；主测试不会偷偷包含答案测试，两个命令都要跑。

## 文件地图与解读

- `comparison.py` / `comparison.js`：完整 Python/JS 调用与执行对照。
- `scheduling.py`：创建、顺序 await、显式调度、阻塞与明确收尾的线程桥接。
- `ownership.py`：取消/超时后的真实临时文件释放。
- `capacity.py`：用 entered/release 门闩证明准入上限。
- `app.py`：上面的完整演示。
- `tests/test_model.py`：事件顺序、文件关闭与拒绝写入、许可复用、真实失败命令。
- `solutions/batch.py` / `solutions/test_batch.py`：独立、有界、可取消的批处理。

JS 对照可选用已有 Node，不要求为 Python 测试安装 Node：

```bash
node comparison.js
uv run --locked python comparison.py
```

预期输出为 expected-javascript.txt、expected-python.txt。Python 调 coroutine 不启动函数体，默认工厂的 Task 显式调度工作，
直接 await 顺序推进，已就绪对象的 await 不必让出。不要拿不稳定耗时推断事件循环进度。

## 真实失败与练习

`uv run --locked python errors/reuse.py` 先打印 42，再以 RuntimeError 退出 1。
`uv run --locked python errors/forgotten.py` 收集真实未 await 警告，工作 events 仍空。
`uv run --locked python errors/swallow.py` 虽退出 0，却显示 pretend-success 和 cancelled=False，是语义失败。
主测试在独立子进程核验这些命令。

引导练习改上限 1 和 3，用 peak 与 active 归零证明，不比耗时。
独立变式先整批验证再产生效果，最多八项，保持输入结果顺序，限制并发和预算，错误/超时/取消后收尾全部孩子。
答案测试检查没有遗留 Task；按输入顺序观察不是 fail-fast 监督。

恢复卡：当前文件、Python/uv 版本、最后成功命令、19+5 中已通过哪组、自己的需求改动、首个反例和下一条聚焦命令。
不要增加任意 sleep 修复顺序，也不要删除其他环境或改共享配置。

## 安全与边界

仅打开临时文件并运行一个明确等待结束的本地工作线程，不访问外部服务、不需要凭证。
取消不能强杀线程或撤销既有效果；事件循环阻塞时不能保证绝对墙钟截止。
Semaphore 限制准入，不限制无限创建 Task 的内存开销。没有性能、生产队列、异步数据库或部署承诺。

## 下载与单一源码约定

DOWNLOAD-ALLOWLIST.json 与仓库同名实验 -files.json 列表一致，只打包这些普通文件。
不包含环境、缓存、凭证或真实业务数据；教材 loader 读取相同源文件。
sources.json 记录官方依据与核验日期，uv.lock 中制品哈希来自 public PyPI 实际解析。
