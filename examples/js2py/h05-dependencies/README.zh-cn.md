# h05-dependencies：完整本地实验

先阅读对应 H05/H06 正文。本目录独立运行，不导入 H04 或旁边实验。
Python、HTML、测试源文件是唯一真源；网页 loader 与下载包使用旁边的
`-files.json` 明确清单，不从整个目录递归收集文件。

## 环境与第一次运行

2026-09-28 实测：CPython 3.13.15、uv 0.12.13、FastAPI 0.135.1、
Uvicorn 0.42.0、Pydantic 2.12.5、Starlette 0.52.1、pytest 8.4.2。
H05 面向学习者的练习不要求 TestClient，也不要求编写 pytest fixture。
有界维护子进程回归仅用 tmp_path 管理临时日志。
要求 Python >=3.13,<3.14；这是应用，因此 uv package=false。
终端进入当前解压目录。锁来自 public PyPI；不要用未经复核的升级替代锁定同步。

```bash
uv sync --locked
uv run --locked python -m pytest -q
TASKS_APP_NAME="Learning tasks" uv run --locked python -m uvicorn task_api.main:create_app --factory --host 127.0.0.1 --port 8005
```

服务会持续运行。另开终端，**仍进入本目录**：

```bash
uv run --locked python live_client.py --port 8005
```

真实客户端要求空的、可丢弃的教学服务，创建测试数据并在 finally 删除。
它检查真实网络、严格拒绝、PATCH 三态、分页、输出过滤及 204/404 清理。
用 Ctrl-C 停服务。清理后可以重跑客户端，但 ID 不必回到 1；只有重启进程才
重建内存数据和编号。不要对已有业务数据执行这个验收。

urllib 客户端逐个尝试自有 ID；某次 DELETE 或读回检查失败会记录下来，
不会跳过后续 ID。结束输出 CLEANUP FAILED 和清理未确认的 ID，重跑前只检查
这些记录。清理失败使程序非零退出；若主体也失败，保留原 traceback 并单独
报告清理诊断，不把任何一种失败伪装成功。不删除其他记录，也不承诺服务不可用
时仍可删净。

## 职责与配置

`task_api/main.py` 组装应用，每个 app 拥有自己的 store；`config.py` 读取和
校验环境字符串；`models.py` 负责输入输出；`store.py` 修改内存而不处理 HTTP；
`routes.py` 将 HTTP 映射为操作；`dependencies.py` 供应 store/settings/page，
并管理每请求一个临时跟踪文件。没有隐藏异步 lifespan、数据库、登录或权限。

TASKS_APP_NAME 是必填非空白的公开显示文本，**不是秘密**。
TASKS_MAX_PAGE_SIZE 默认 100，接受 20..100 的 ASCII 十进制整数；下界保证
默认分页 20 始终合法。配置在每次调用工厂时读取一次，不在每请求读取。
不会自动加载 `.env`。修改运行配置需要停止并以新环境重启。
直接构造 Settings 是可信内部测试输入，不是外部配置校验接口。

```bash
env -u TASKS_APP_NAME uv run --locked python -m uvicorn task_api.main:create_app --factory --host 127.0.0.1 --port 8005
TASKS_APP_NAME="Learning tasks" TASKS_MAX_PAGE_SIZE=bad uv run --locked python -m uvicorn task_api.main:create_app --factory --host 127.0.0.1 --port 8005
```

这两条是**预期启动失败**，不是 API 验收通过。末行诊断指出 TASKS_APP_NAME
或 TASKS_MAX_PAGE_SIZE，但不回显原值。修好变量，重放第一条成功启动命令。
端口占用时停止自己的旧服务或换端口，不杀不明进程。导入错误先查工作目录与
`task_api` 文件是否完整，改 CORS 不能修复导入错误。

## 契约与局限

POST /tasks 返回 201；列表和 GET/PATCH /tasks/{id} 返回 200；DELETE 返回
204 空正文。不存在的正整数 ID 返回 404，非法输入返回 422。ID 由服务器分配。
标题 1..120 字符、拒绝全空白、保留原字形和空格；minutes 是普通非负 JSON
整数，拒绝 bool/str/float；done 是严格 bool，默认 false；note 是可空文本，
最多 1000 字符，默认 null。PATCH 区分遗漏/赋值/null，只有 note 可以 null。
拒绝多余请求字段；输出不含 internal_tag。列表返回 items/limit/offset/total，
按 ID 排序；offset 数的是记录而不是 ID。limit 为 1..100 并遵守配置上限。

TRACE acquire/use/release 对应真实 TemporaryFile 句柄，不是持久审计日志或
数据库事务。显式 function scope 在正常响应发送前释放；关闭资源不回滚修改。
不承诺生产并发、持久化、用户隔离、部署、网络安全、身份验证或授权。
只监听 127.0.0.1；实验没有真实用户数据和凭证。

## H05 独立变式

不看 solutions，添加独立 include 的 GET /summary 路由，返回 total/done/minutes，
复用同一 store 依赖，统计全部记录而不是一页。验收空数据、创建、PATCH、删除；
不能新建第二份全局 store 或硬编码汇总。正常套件 17 项（15 项配置/store + 2 项清理回归）；答案 2 项函数测试，
还必须运行下面的真实 HTTP 场景。先停止原服务，再用同端口启动答案；第二个
终端执行客户端。

```bash
uv run --locked python -m pytest -q solutions/test_summary.py
TASKS_APP_NAME="Summary tasks" uv run --locked python -m uvicorn solutions.summary:create_summary_app --factory --host 127.0.0.1 --port 8005
```

```bash
uv run --locked python live_client.py --port 8005 --summary
```

## 有界维护回归

```bash
uv run --locked python -m pytest -q tests/test_live_client_cleanup.py
```

预期 `2 passed`。两项在操作系统分配的本地端口启动自有故障服务器，运行真实
客户端。首个 DELETE=503 不能跳过第二个 ID；只剩第一个且客户端非零退出。
第二项还让主体失败，并检查原 traceback 保留。finally 停自己的服务器，
不接触用户已有服务。这个维护工具不是独立练习先修，不要求异步测试代码。

## 打包、暂停恢复与证据

只有旁边 allowlist 中的文件进入下载包。明确排除 .venv、__pycache__、
.pytest_cache、.env/.env.*、日志、凭证、编辑器状态、临时文件及本地缓存。
不要递归压缩目录。包含 uv.lock，但不包含解释器安装和缓存。三语 README
保持命令与输出不变。

暂停记录工作目录、版本、最后命令及真实结果、服务 PID/端口与是否停止、
数据现状、未解决失败及下次第一步。恢复先锁定同步与正常测试，再重放具体
失败请求。Python 语法通过不是 HTTP 验收。

SOURCES.md 记录实时核验的一手来源与版本/scope 细节。仓库可选维护脚本
`scripts/test-js2py-http-foundations.py` 检查 allowlist 干净副本、两套测试、
预期失败、真实本地服务、资源发送时序和进程清理；它不是读者先修，也不替代
真实浏览器检查。生产、数据库、TLS、压测行为均不在本实验的验证范围。
