# H03 — 第一个同步 FastAPI 服务

[English](README.md) · [繁體中文](README.zh-tw.md)

这是独立的本地只读任务 API 实验。前置为 H02 的 HTTP 与 L13 的装饰器，不假定已有后端框架经验，也不导入其他章节实现。网页正文解释机制，本 README 随源码保存可运行契约。

## 环境与工作目录

**2026-09-28** 在 macOS arm64 实测：CPython **3.13.15**、uv **0.12.13**、FastAPI **0.135.1**、Uvicorn **0.42.0**、Pydantic **2.12.5**。这是固定验收版本，不是“最新”承诺。`uv.lock` 来自公开 PyPI，固定间接依赖，包括 Starlette 1.7.0、pydantic-core 2.41.5。`requires-python` 为 `>=3.13,<3.14`；`[tool.uv] package=false` 表示运行本地文件，不构建安装当前项目。无需前端依赖、API key、数据库、pytest 或 httpx。

进入解压的 `h03-first-fastapi`；仓库内则进入 `examples/js2py/h03-first-fastapi`。下面命令均在此目录执行。

```bash
uv --version
uv python install 3.13.15
uv sync --locked
uv run --locked python --version
```

维护者隔离复现时，在执行 uv 前导出：

```bash
export PATH="$HOME/.local/bin:$PATH"
export UV_PYTHON_INSTALL_DIR=/tmp/langshift-js2py-python-20260928
export UV_CACHE_DIR=/tmp/langshift-js2py-uv-cache-20260928
```

这些 `/tmp` 目录是可丢弃基础设施，不属于交付项目；普通读者可以使用 uv 默认位置。为了运行实验不要重新生成锁文件。维护者使用 `uv lock --default-index https://pypi.org/simple` 解析，安装和执行使用 `--locked`。

## 启动、请求、退出

终端 A：

```bash
uv run --locked python -m uvicorn app:app --host 127.0.0.1 --port 8003 --workers 1
```

`app:app` 从此目录导入模块 `app`，取得其中的 `app` 对象。导入登记路由，Uvicorn 才打开监听。`python app.py` 只执行定义随后退出。显式 `--workers 1` 避免继承外部工作进程设置，但不表示同步处理函数串行运行。本次不要使用 reload；更不要把无认证服务绑定到 `0.0.0.0`。

终端 B：

```bash
curl -sS -i http://127.0.0.1:8003/health
curl -sS -i http://127.0.0.1:8003/tasks/1
curl -sS -i 'http://127.0.0.1:8003/tasks?limit=1&offset=1'
bash requests.sh
```

`-sS` 隐藏进度但显示连接错误；`-i` 显示状态和头；查询 URL 的 `&` 要用引号保护。工作单有 **11** 个可见请求，打印证据但不自动判定通过。curl 默认进程退出码并不保证 HTTP 成功。API 自动测试与 fixture 到 H06 才正式教学。

单项请求预期：

```http
HTTP/1.1 200 OK
content-type: application/json

{"id":1,"title":"Read HTTP","minutes":25,"done":false,"note":null}
```

以上省略动态响应头。第二页只包含 id=2，`limit=1`、`offset=1`、`total=2`。退出时在终端 A 按 Ctrl-C，只关闭自己启动的前台服务；再请求会连接失败，而不是收到 404。

## 接口契约

- `GET /health`：200，`{"status":"ok"}`。这是进程存活，不是数据库就绪。
- `GET /tasks`：200，`{items, limit, offset, total}`，按 id 升序。limit 默认 20，范围 1–100；offset 默认 0，非负。超出末尾是空页 200；`total` 是全部记录数。
- `GET /tasks/{task_id}`：解析后的正整数，id 1/2 返回 200；合法但不存在返回 404 和 `{"detail":"Task not found"}`；文本或非正数为 422。
- 没有写操作。`POST /tasks` 为 405；未知路由为 404、`Not Found`。
- 公开字段 `id`、`title`、`minutes`、`done`、`note`，衔接 H04，但本章不教请求体模型。
- `/docs` 与 `/openapi.json` 暴露生成契约，能打开文档不等于行为验收通过。

## 故意失败与恢复

1. 保持自己的服务运行，在另一个终端重复启动。第二个进程非零退出，报 `address already in use`；原服务仍响应 `/health`。不要杀别人的监听进程；停止自己启动的服务，或换空闲端口并同步修改客户端 URL。
2. 退出自己的服务，在实验父目录执行：

   ```bash
   uv run --project h03-first-fastapi --locked python -m uvicorn app:app --host 127.0.0.1 --port 8003 --workers 1
   ```

   预期 `Could not import module "app"`。找到项目环境没有改变工作目录。恢复为进入实验目录，或在父目录加 `--app-dir h03-first-fastapi`。改成 `app:missing` 则报 `Attribute "missing" not found`，需要分别核对冒号两侧。
3. 在实验根目录启动明确的错误应用：

   ```bash
   uv run --locked python -m uvicorn errors.broken_app:app --host 127.0.0.1 --port 8003 --workers 1
   ```

   终端 B 执行 `curl -sS -i http://127.0.0.1:8003/broken`。应为 500，正文 `Internal Server Error`，服务端回溯含 `RuntimeError: deliberate failure for H03`。退出它，重新启动 `app:app`，复验 `/health` 与 `/tasks/1` 均为 200。启动失败、输入 422、缺失 404、程序 500 属于不同层。

## 独立任务与恢复笔记

只带环境文件和上述契约，在新目录重建服务，解释导入、注册、验证、处理、JSON 序列化。再加 `/summary`，统计未完成任务 count/minutes，应得 `{"count":1,"minutes":25}`。先尝试，后看独立参考；参考自带种子与路由：

```bash
uv run --locked python -m uvicorn solutions.rebuild:app --host 127.0.0.1 --port 8003 --workers 1
```

笔记保存工作目录、应用入口、最后成功命令、请求/状态/正文、端口及所属终端、未解决问题、下次命令，并记录服务是否已停。这里的只读种子在导入时重建，不是保存过的用户数据。

## 文件、打包与边界

- `app.py`：完整服务；`requests.sh`：可读 HTTP 工作单。
- `errors/broken_app.py`：故意 500；`solutions/rebuild.py`：独立答案。
- `.python-version`、`pyproject.toml`、`uv.lock`：可复现环境。
- `README*.md`、`SOURCES.md`、`VERIFICATION.md`：操作说明、官方依据、实际证据。

同级 **h03-first-fastapi-files.json 是明确正向 allowlist**，页面和下载只使用列出的文件。禁止递归压缩目录：排除 `.venv`、`__pycache__`、缓存、`.env`/凭证、日志、编辑器文件和个人数据。`.gitignore` 只是补充，不替代下载白名单。共享 loader/ZIP 由集成者统一接入。

验收仅覆盖本地、单工作进程、顺序请求、固定只读数据；不提供并发、身份权限、生产部署、浏览器 CORS、代理/TLS、性能、跨平台保证。Python 语法通过不是 API 验收。实跑 case 见 **VERIFICATION.md**，2026-09-28 核验的官方来源见 **SOURCES.md**。
