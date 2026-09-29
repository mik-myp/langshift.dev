# H01：从客户端到持续运行的服务

状态：本地实验，不是任务 API 或可部署后端。核验日期 2026-09-28。

## 目标与范围

前置为 L10 本地工程和 L14 资源生命周期。你将启动一个进程、观察 loopback 监听、追踪请求到文件的路径，区分请求完成与进程退出，定位 404/连接失败/端口冲突，并只停止自己的服务。不要求实现 HTTP 服务器、FastAPI、数据库、认证或异步。

只公开 `public` 或参考 `solutions/public`。不要公开工程根、用户目录、凭证、`.env` 或符号链接。`http.server` 会跟随符号链接且可能列出目录，不是安全沙箱；loopback 不是身份验证。

## 环境与工作目录

固定 CPython 3.13.15（`.python-version`），范围 `>=3.13,<3.14`；开发依赖 pytest 8.4.2；实测 uv 0.12.13、macOS、curl 8.7.1。无第三方运行依赖。命令为 macOS/Linux shell；未验收 Windows 的终端与信号行为。

仓库用户先从仓库根进入下面目录。下载用户进入解压后的 `h01-service-process`，从 `uv sync` 开始。

```bash
cd examples/js2py/h01-service-process
pwd
uv sync --locked --default-index https://pypi.org/simple
uv run --locked python --version
uv run --locked python one_shot.py
uv run --locked python observe.py
uv run --locked python -m pytest -q
uv run --locked python -m solutions.observe_health
uv run --locked python -m pytest -q solutions/test_health.py
```

`observe.py` 的稳定输出：

```text
200 hello from the service
404 missing
200 hello from the service
request_done_process_alive=True
process_stopped=True
```

标准 13 项、独立参考 2 项通过。独立参考访问 health 返回 `ready`，404 后再请求仍成功。自动工具只监听 `127.0.0.1`，让操作系统选择端口，并在 finally 中清理自己创建的子进程。测试证明列出的本地行为，不证明生产并发、外网安全或持久化。

## 两个终端，真实请求

A、B 都位于实验根。A 前台启动：

```bash
uv run --locked python -m http.server 8765 --bind 127.0.0.1 --directory public
```

`-m` 运行标准库模块；`8765` 为端口；`--bind` 限定 loopback；`--directory` 指公开目录，相对 A 的启动工作目录。提示符不回来是服务等待请求的正常行为。

B 发出请求：

```bash
curl --noproxy '*' --max-time 3 --verbose 'http://127.0.0.1:8765/hello.txt'
curl --noproxy '*' --max-time 3 --include 'http://127.0.0.1:8765/not-here.txt'
echo $?
uv run --locked python client.py 8765 /hello.txt
```

curl 是客户端，不监听服务端口。`--noproxy '*'` 绕过代理，引号防止 shell 展开星号；`--max-time 3` 限制整轮传输；`--verbose` 把连接/头部诊断写到标准错误；`--include` 把响应头和正文一起显示。先看到 200 与 `hello from the service`，再看到 404 的 HTML 错误页。默认 curl 收到 HTTP 错误仍可退出零；`echo $?` 是命令退出状态，不是 HTTP 状态。Python 客户端成功为零、HTTP 错误退出 2、连接异常退出 1。

回到 A 按 Ctrl+C，只停止这个前台实例。B 再请求原 URL，在端口无人接管的实测条件下 curl 退出 7，没有 HTTP 响应。恢复用原启动命令。禁止 `killall`、按端口杀陌生进程、开放 `0.0.0.0` 或加公网隧道。

## 失败定位与练习

- `Address already in use` 是启动阶段获取监听失败。确认自己的旧实例，不能确认就换 `8766` 并同步所有客户端；不停止不明进程。
- 404 表示有 HTTP 响应，检查路径与公开目录，而非重装 Python。把公开目录换为 `solutions/public` 会让 `/hello.txt` 404、`/health.txt` 200。
- 连接失败发生在 HTTP 响应之前，检查自己的进程、主机和端口。停止自有服务再重试可以复现，不探测他人的服务。
- 独立任务：用另一个公开目录和端口完成 health 成功、缺失路径失败、note 成功，并证明旧 hello 不共享。先自己完成，再看 `solutions`。

解释题答案：客户端退出只结束自己；服务继续持有监听资源。404 不能证明资源存在，也不能单独证明响应者是预期实例。前端禁用输入框无法约束其他客户端；后续必须由服务端验证与授权。

## 暂停恢复与文件说明

记录工作目录、公开目录、端口、拥有服务的终端、最后成功/失败命令、失败层次、13+2 项测试结果与下次第一步；暂停前停止自己的实例。恢复先跑 `observe.py`，再重做手动成功/失败/成功，不拿旧笔记 PID 随意杀进程。

`client.py` 是单次 HTTP 客户端；`observe.py` 是生命周期观察；`tools/owned_server.py` 是有超时的测试基础设施，不是学生必须重建的服务器实现。它只使用标准库 CLI，绝不按端口扫描或停止其他程序。`tests` 是默认套件，`solutions` 是独立参考。下载由外部同名 `-files.json` 显式清单生成；不包含 `.venv`、缓存、临时日志或凭证。

## 一手资料

2026-09-28 核对：[http.server](https://docs.python.org/3.13/library/http.server.html)、[http.client](https://docs.python.org/3.13/library/http.client.html)、[subprocess](https://docs.python.org/3.13/library/subprocess.html)、[curl](https://curl.se/docs/manpage.html)、[RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)、[IANA loopback](https://www.iana.org/assignments/iana-ipv4-special-registry/iana-ipv4-special-registry.xhtml)、[WHATWG URL](https://url.spec.whatwg.org/)。没有验收公网、TLS、浏览器跨源策略、数据库或生产部署。
