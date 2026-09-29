# D05：保留已有数据的可审查迁移

本地多文件实验，不能在 Pyodide 运行。当前目录就是完整 canonical 源码，不导入相邻实验。
网页与下载使用显式 `d05-migrations-files.json` allowlist，不能把整个工作目录递归打包。

## 1. 第一次运行前，分清解释器、驱动与服务

先在终端进入解压后的 `d05-migrations` 目录。CPython 执行 Python；uv 把锁定依赖装入 `.venv`，
但它们不会安装或启动 PostgreSQL 服务。`postgres` 是数据库服务进程，`initdb` 初始化
一个新集群，`pg_ctl` 管理指定集群，`psql` 是命令行客户端。四个二进制应来自同一套 18 版本安装。
`psycopg[binary]` 自带客户端库，并不包含数据库服务器。

实测机器为 macOS arm64，Python 3.13.15、uv 0.12.13、PostgreSQL 18.6，二进制位于
`/opt/homebrew/bin`。若缺少工具，先依 SOURCES.md 的官方安装页面安装 uv 与 PostgreSQL 18
二进制；不要初始化已有目录，不启动系统服务。其他 POSIX 系统把 PG_BIN 改成这四个程序
所在目录的绝对路径；下面的 Homebrew 路径不是所有系统通用。不要用 root 运行。
本实验依赖 Unix socket，未验证 Windows。无需 Docker、`brew services`、云账号或密码。

## 2. 安装锁定依赖并运行

下面两个临时 uv 目录隔离这台共享机器上的解释器/缓存，不是数据库数据目录。
`uv sync --locked` 不应偷偷改锁；锁从 public PyPI 真正生成。Python 范围为
`>=3.13,<3.14`，`[tool.uv] package=false`。

```bash
export PATH="$HOME/.local/bin:$PATH"
export UV_PYTHON_INSTALL_DIR=/tmp/langshift-js2py-python-20260928
export UV_CACHE_DIR=/tmp/langshift-js2py-uv-cache-20260928
export PG_BIN=/opt/homebrew/bin
uv --version
"$PG_BIN/postgres" --version
uv python install 3.13.15
uv sync --locked
uv run --locked python pg_sandbox.py --evidence /tmp/d05-migrations-cleanup.json -- python -m pytest -q
uv run --locked python pg_sandbox.py -- python history_demo.py
```

预期 **9 passed**，耗时和临时路径会变化。SQLAlchemy 2.0.54 是有意选择的 2.0
维护线，不把它说成当前功能主线：2026-09-28 已有 2.1.1。固定 Alembic 1.20.0、
psycopg/psycopg-binary 3.3.6、FastAPI 0.135.1、Uvicorn 0.42.0、Pydantic 2.12.5, HTTPX 0.28.1、pytest 8.4.2；
间接依赖见 `uv.lock`。Web 版本与 H03–H06 统一，不在 ORM 章节无声升级框架。Starlette 0.52.1 与 AnyIO 4.12.1 也对齐 H05/H06 的实测锁。

## 3. 服务到底在哪里，谁负责关掉

`pg_sandbox.py` 在 `/tmp/ls-pg-*` 用 mkdtemp 建立独占集群。集群是一份 PostgreSQL
服务数据目录，里面可有多个数据库；测试数据库是该集群内隔离的一份对象集合。
服务只监听私有 Unix socket，目录和 socket 权限为 0700，不开放 TCP。
本地 trust 仅适用于这份同一系统用户掌控的短命实验，不是生产安全方案。
marker/token 防误接库，不防同一 OS 用户下恶意进程。

脚本依次 initdb、对独占目录 pg_ctl start、创建非超级用户 lab_owner（有 CREATEDB，
供 fixture 建库）、创建随机 js2py_lab_* 数据库。继承的 PG 设置、开发/测试 URL 会被移除。
只有子命令得到 LAB_DATABASE_URL 和所有权标记。safety.py 会拒绝普通开发/生产连接，
不是换个环境变量名便允许危险操作。每个测试另建数据库，归还连接、dispose 连接池，
再删除自己那一库；不使用 DROP FORCE 掩盖连接泄漏。

finally 用 fast shutdown 停自己的服务，检查 pg_ctl status 返回 3（未运行），再删自己的
目录。清理 JSON 中应有 server_version=180006、stopped=true、removed=true、status_after_stop=3。
子命令失败也会清理；停止失败则保留目录与日志并报错，不能随手杀所有 postgres 进程。
SIGKILL/断电无法执行 Python finally；这时只能检查输出中的精确独占目录与进程再人工恢复。

每次 wrapper 调用都是新集群。若需要连续执行多条命令，使用
`uv run --locked python pg_sandbox.py -- bash`，在这个子 shell 内操作，最后 `exit`。
普通 shell 不会永久得到数据库配置。实验临时性不代表生产服务应该丢弃数据。

## 4. 先定位，再恢复

| 观察 | 检查与处理 |
| --- | --- |
| 找不到 PostgreSQL / 主版本错误 | 检查四个程序和 PG_BIN，不改接现有服务。 |
| Refusing database access | 使用 wrapper；不要删除保护条件，也不要改接开发库。 |
| relation does not exist | D04 在同一个 sandbox bootstrap；D05/D06 对这一库 upgrade，不是对上次已经删除的库。 |
| PendingRollbackError / Session 已失败 | 结束失败工作单元，rollback 或丢弃 Session；不能只重试最后一条 INSERT。 |
| pool timeout / 数据库仍有连接 | 关闭所有 Session/Connection，再 dispose；扩大池会掩盖泄漏。 |
| 迁移拒绝旧数据 | 检查 revision 和异常行，按明确业务规则修正后重跑，不用 stamp 跳过失败。 |
| stopped=false | 保留证据/server.log；只停输出中自己的集群，停止确认前不删目录。 |

## 5. 模型衔接与边界

四表和原约束名与 D01–D03 一致。H 的 done=false/true 映射 todo/done，doing 为新增状态；
note 改为可空 description，minutes 保留估算；数据库 bigint identity 替代内存 ID 分配，
没有偷偷导入旧 ID。显式加入 Project/User/ProjectMember 和任务外键。
updated_at 不会自动更新，SQL btrim 也不等于 Python 的全部 Unicode 空白规则。
所有外键为 RESTRICT。D05 经可空扩展、回填、默认值/NOT NULL/CHECK 增加 priority。
D06 保持该 head，复合索引是独立测试库内实验，不是隐藏的下游结构变更。

这里不是已完成鉴权的多用户服务。后续 S 章节必须迁移密码哈希、启用状态、auth_version，
从验证后的身份推导创建者，并实施成员与负责人规则；外键存在不等于有权限。
没有验证生产性能、零停机迁移、网络分区恢复、备份和授权。先做正文任务，再看 solutions。

## 6. 暂停与恢复记录

记录代码差异、当前章节/revision、最后成功命令、已通过测试、未解决问题、下次第一步。
wrapper 退出后临时集群不保留：保存生成数据的命令，不复制数据库目录。
`.venv`、`.pytest_cache`、`__pycache__`、`.env`、DB data、日志、真实秘密都不能进入下载包。
官方资料核验与实际执行基线：**2026-09-28**，详见 SOURCES.md。
