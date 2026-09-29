# A02 — 外部服务生命周期

核验日期 2026-09-28。这是位于 S03 后的独立本地实验，不是完整 capstone，
不导入其他章节源码。前置为 Python 函数、异常、上下文管理器、测试和已有的
同步 API/SQL/认证基础；A02 另以 A01、L14、H05 为前置。

## 从干净下载复现

解压后进入 `a02-external-services`；仓库中进入 `examples/js2py/a02-external-services`。
固定 CPython 3.13.15、uv 0.12.13、pytest 8.4.2，先安装指定 uv，本实验不替你升级工具。
FastAPI 0.135.1, Uvicorn 0.42.0, Pydantic 2.12.5, HTTPX 0.28.1, AnyIO 4.12.1, Starlette 0.52.1.
Web 框架沿用 H03–H06 基线，生命周期依赖沿用 H05–H06。
真实 public-PyPI lock 含解析结果和制品哈希，requires-python 只接受 3.13，
`tool.uv.package=false` 表示直接运行本地源码，不安装本项目为包。
不要删锁或无声升级框架。

```bash
# Run from the extracted a02-external-services directory.
set -eu
export PATH="$HOME/.local/bin:$PATH"
export UV_PYTHON_INSTALL_DIR=/tmp/langshift-js2py-python-20260928
export UV_CACHE_DIR=/tmp/langshift-js2py-uv-cache-20260928
uv --version
uv python install 3.13.15
uv sync --locked
uv run --locked python --version
uv run --locked python socket_lab.py
uv run --locked python -m pytest -q
uv run --locked python -m pytest -q solutions
```

两个 /tmp 目录隔离解释器与下载缓存，不保存业务数据。安装锁定公共依赖需要联网，
实验运行不访问收费/第三方服务、不发送用户数据。

## 稳定演示输出

输出以 `expected-socket-output.txt` 为源，实际运行必须匹配。

```text
socket: normal hint available; upstream connection reused
socket: unavailable -> unavailable; core read ok
socket: malformed -> unavailable; core read ok
socket: wrongshape -> unavailable; core read ok
socket: oversized -> unavailable; core read ok
socket: slow -> unavailable; core read ok
socket: core create/update/read/delete finished while upstream held
socket: lifespan client closed
```

主测试 **32 passed**，独立答案测试 **4 passed**。耗时不是正确性断言。
除故意收集警告的诊断外，警告视为错误；主测试不会偷偷包含答案测试，两个命令都要跑。

## 文件地图与真实证据

- `lifecycle.py`：回环 allowlist、共享客户端、阶段超时、有界清理保护。
- `app.py`：显式 lifespan、合成内存 CRUD、单独的可选提示接口。
- `service.py`：整次操作预算、共享准入上限、最多两次只读 GET、正文上限、严格验证、脱敏降级与取消传播。
- `faults.py`：测试专用 ok/unavailable/flaky/malformed/wrongshape/oversized/slow/hold 场景。
- `socket_lab.py`：两个绑定自动分配 127.0.0.1 端口的真实 Uvicorn 服务。
- `tests/test_service.py`：27 项政策/ASGI/诊断测试；替身不能证明真实网络计时。
- `tests/test_socket.py`：5 项真实 TCP 测试，正常/异常/取消后的对端 EOF、关闭后拒绝使用、取消单次借用后容量仍可复用。
- `solutions/receipts.py` 及测试：丢回复与幂等练习，以及重启不持久的反证。

手动服务器分别开两个终端，从同一个实验根启动：

```bash
uv run --locked uvicorn faults:create_fault_app --factory --host 127.0.0.1 --port 8766
uv run --locked uvicorn app:create_app --factory --host 127.0.0.1 --port 8765
```

默认上游端口 8766，只用合成任务文本；/control 只供测试。结束时只在自己的两个终端按 Ctrl-C。
端口冲突时用 socket_lab.py，不杀不认识的进程；自动实验只停止自己持有的 Server 并关闭自己的 socket。

## 故障、练习与恢复

`uv run --locked python -m errors.config` 应退出 1，最后一行异常脱敏；源码中的 URL 明确为假。
原始 traceback 仍可能带源码行，不能公开返回。
`uv run --locked python -m errors.untrusted` 应退出 1 并报告 ValidationError，说明可解析 JSON 不等于可信数据。

引导修改：仅一次尝试、一个并发操作；更新政策次数断言，不篡改替身行为。
独立变式：以固定幂等键重现回复丢失，同 key/正文只产生一次效果，不同正文冲突，取消不重试，重启揭示内存账本不持久。

恢复卡：当前文件、版本、最后成功命令、32+4 中已通过哪组、首个失败场景、下次只跑哪个测试。
app.state 缺失先查 lifespan；正常请求报 client closed 则查是否请求误关共享对象。

## 安全与未证明边界

只接受明确的 http://127.0.0.1:<port>，无真实凭证、用户数据、收费服务或环境秘密读取，不跟随重定向，禁用 HTTPX 代理继承。
CRUD 仅在内存、重启丢失且没有认证授权，不能公开暴露或替代 capstone 的 SQL/权限设计。

读取空闲超时有真实 socket 证据；connect/write/pool 故障政策含替身测试，不是所有网络阶段已实际验证。
没有验证 TLS、真实 DNS、HTTP/2、多 worker 容量、进程强杀或其他 AnyIO 后端。
测试显式取消拥有者 Task，不声称每次 HTTP 断开都会取消 handler。
BackgroundTasks 与内存队列不是持久投递系统。

## 下载与单一源码约定

DOWNLOAD-ALLOWLIST.json 与仓库同名实验 -files.json 列表一致，只打包这些普通文件。
不包含环境、缓存、凭证或真实业务数据；教材 loader 读取相同源文件。
sources.json 记录官方依据与核验日期，uv.lock 中制品哈希来自 public PyPI 实际解析。
