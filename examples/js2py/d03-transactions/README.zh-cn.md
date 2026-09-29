# d03-transactions — 事务、失败恢复和真实并发

核验日期：2026-09-28。独立下载实验，全部使用真实 PostgreSQL，不能用 SQLite 或浏览器 Python 替代。完整教材是 `module-23-transactions` 的三语版本。

## 目标与前置

前置 L00–L14、H01–H06；D02 另需 D01，D03 另需 D02。D01 学习者不需提前会 SQL 或运维。先读教材中的机制解释再执行本文件；README 是可重建运行指南，不把安装成功当掌握。

本实验验收 事务、失败恢复和真实并发。模型版本 `d01-d03-v1`；`model-contract.json` 给出字段与 ORM 衔接，`sql/schema.sql` 是可执行 DDL。身份/权限尚未实现：users 是测试人员，不是可登录账号。旧 H 字段明确演进：done 变 status（todo/doing/done），note 变 description（可空），minutes 保留为非负估时；新增用户、项目、成员和时间字段。这不是对已有内存数据自动迁移。

## 固定环境，不安装系统服务

- PostgreSQL 18.6（本机 Homebrew，服务端实际 `server_version_num=180006`）；官方发布日期 2026-08-13。
- CPython 3.13.15，uv 0.12.13，pytest 8.4.2，psycopg[binary] 3.3.6。
- `requires-python = ">=3.13,<3.14"`；uv package=false；公共 PyPI 的真实 uv.lock。
- 仅 macOS/Homebrew 环境已实测；其他 OS 安装、TCP/TLS 和生产配置未实测。无 Docker、ORM、认证、前端依赖。

工作目录必须是解压后的 `d03-transactions`，不是上级目录。此机器工具已有，**不要 brew services，不要连接默认 5432，不要初始化现有目录**。

```bash
export PATH="$HOME/.local/bin:$PATH"
export UV_PYTHON_INSTALL_DIR=/tmp/langshift-js2py-python-20260928
export UV_CACHE_DIR=/tmp/langshift-js2py-uv-cache-20260928
export PG_BIN=/opt/homebrew/bin
"$PG_BIN/postgres" --version
"$PG_BIN/initdb" --version
"$PG_BIN/pg_ctl" --version
"$PG_BIN/psql" --version
uv --version
uv sync --locked
uv run --locked python --version
```

版本不匹配先停下。`PG_BIN` 是程序目录；`psql` 是客户端；`postgres` 是服务器；`initdb` 只创建新存储；`pg_ctl` 按明确目录启动/停止进程。安装物、运行进程、数据目录不是一件事。

## 认领独占集群与数据库

```bash
uv run --locked python labctl.py start
uv run --locked python labctl.py status
uv run --locked python labctl.py dsn
uv run --locked python labctl.py reset --yes-reset
```

start 的具体顺序：新建短路径 `/tmp/lsdb-*`（macOS 可显示 /private/tmp）；目录和 socket 均 0700；保存匹配的 `.lab-state.json` 与目录 marker；initdb 新目录；关闭 TCP；为私有 socket 选端口；pg_ctl 用显式 -D 和 server.log 启动；随机管理角色建立 `langshift_lab` 数据库和普通 `lab_student` 角色。数据库是 cluster 内的逻辑命名空间，角色是数据库身份，不是 users 表的用户。Unix socket 是通信入口，DSN 是地址/选项，连接才是活动会话。

本地 trust 仅因目录私有且 TCP 禁止才用于无密码练习；同一 OS 用户下的进程和 root 不在隔离范围内，不能复制到公网或生产。连接、reset、stop 都验证所有权；SQL 连接还验证服务端数据目录、系统标识和版本。脚本忽略 DATABASE_URL，不接受任意远端 DSN；不要修改这些防护。

reset **有损重建自己数据库的四表**，打印 `schema + seed ready: users=2 projects=3 members=4 tasks=5`。每次业务 pytest、D03 demo 也会 reset，因此不要并行启动两个运行器，不要拿这里保存业务数据。停启不会 reset；系统可能清理 /tmp，所以它仍不是长期保存或备份方案。

## PostgreSQL 环境边界

`labctl.py` 自身在启动或任何 SQL 连接前检查环境，直接通过 Python 导入调用也一样：**拒绝除 `PG_BIN`、`PGHOST` 外的全部 `PG*` 变量**，包括空值和未知名称。这也会保守拒绝虽已被显式覆盖的 `PGPORT`、`PGUSER`、`PGDATABASE`，不只 `PGHOSTADDR`、`PGSERVICE`、`PGSERVICEFILE`、`PGPASSFILE`、`PGPASSWORD`、`PGOPTIONS`。错误只列变量**名**，不打印值。启动或执行 SQL 前，在实验 shell 中 unset 报出的变量；不要把其他服务配置或凭证复制进实验。

`PG_BIN` 仍用于选择工具目录。`PGHOST` 仍被接受但忽略，因为每条 DSN 都显式指定自有私有 socket；维护 runner 的 `PGHOST=/nonexistent/...` 验证仍成立。`DATABASE_URL` 仍忽略。所有子进程（包括 initdb、pg_ctl、psql）都使用清除全部 `PG*` 和 `DATABASE_URL` 的环境，工具和数据路径显式指定。Python 连接不临时修改进程环境，因此 D03 并发连接不存在环境恢复竞态。

管理员和学生的每条 DSN 均显式指定自有 root 下**内容为空、权限 0600 的 `empty.pgpass`**，不使用默认 `~/.pgpass`。新集群和已有自有集群均可创建该文件；符号链接、非空、属主错误、非普通文件或权限错误均拒绝。psql 同时使用 `-X -w`（不读启动文件、不提示输入密码）。随机管理员及服务端数据目录／系统标识／版本核验保留，不改业务 SQL。

**错误的连接环境不阻止清理：** `status` 使用清洁环境调用 pg_ctl；`stop` 在清洁 Python 子进程中完成相同的服务器身份核验，再停止显式指定的自有数据目录。不会绕过 marker／PID／身份检查失败。停止后须清除报出的变量才能重新 start。导出的 `dsn` 只是连接描述，不是沙箱：不要交给继承其他连接默认值的任意客户端；请使用 `labctl.py psql`。

`tests/test_environment.py` 新增 50 例：连接／启动前 mock 拒绝、子进程环境、passfile、面对自有 loopback 监听器的直接 CLI 拒绝、私有 socket 下 PGHOST／DATABASE_URL 兼容，以及污染环境下 stop／status／重新启动恢复。该模块覆盖业务测试的自动 SQL reset fixture，避免负向测试在拒绝前先连接。这里只验证列出的路径，不声称覆盖所有攻击；同一 OS 用户／root 对进程或文件的篡改不在隔离范围内。

## 运行、解释和验收

```bash
uv run --locked python labctl.py psql --file sql/failed_transaction.sql
uv run --locked python demo.py
uv run --locked pytest -q
```

应有 **63 passed**（原 13 例业务测试 + 50 例环境测试），耗时不固定。故意错误 SQL 的 ERROR 是预期；普通命令失败不能被忽略。D01：23505 重复、23503 坏外键、23514 CHECK、23502 NULL、22001 长度；本版本删除引用的 RESTRICT 是 23001。D02：注入载荷作为原字符串保存，tasks 不被删除；非法排序/分页在 Python 拒绝。D03：后步 23503，后续查询 25P02，rollback 后零残留；真实两连接的结果分别为读提交 [30,40]、可重复读 [30,30]、丢失更新 37、原子累加 42、唯一竞争一行、锁超时 55P03、旧快照更新冲突 40001 后完整重试 42。

`demo.py` 的输出以教材为准，D02 确定 ID 需要先 reset；D03 每个场景自己 reset。测试不是编译：实际启动的服务器执行了约束、参数和值转换、事务与锁。独立题参考在 answers 中，先自己尝试；不是主模型新增字段，也没有自动接入 HTTP。

## 文件职责

- `labctl.py`：独占启动、地址、身份验证、reset、psql、stop；无全局服务操作。
- `sql/schema.sql` / `sql/seed.sql`：三章相同结构与确定种子；DDL 哈希在 model-contract。
- `sql/*.sql`：本章查询或明确标记的失败实验。
- `tests/`、`conftest.py`：业务测试每例重置自己的数据库；参考变式也执行验证。
- `answers/`：独立题参考，不要先抄。
- `pyproject.toml`、`uv.lock`、`.python-version`、`.env.example`：依赖与配置；env.example 仅文档，不自动加载。
- `README.md`、`README.zh-cn.md`、`README.zh-tw.md`、`sources.json`、`model-contract.json`：复现、来源和衔接。
- `FILES.json`：包内文件 allowlist；仓库同名 `../d03-transactions-files.json` 用于主线打包。数据目录、.lab-state.json、.venv、cache 和凭证不进入包。

## 安全停机与恢复

```bash
uv run --locked python labctl.py stop
uv run --locked python labctl.py status
uv run --locked python labctl.py start
uv run --locked python labctl.py stop
```

stop 先核对 marker/PID 目录/健康服务器身份，然后对自己的 -D 执行 fast shutdown 并等待；status 返回 running=false、pg_ctl_status=3。fast 会断开本集群连接并回滚未提交事务，保留提交数据与日志；不对其他 postgres 发信号，不 brew services，也不删目录。停止后重新 start 是恢复同一存储，不是 initdb。

若连接失败先查 status 与所打印 root 的 server.log；若版本错查 PG_BIN；若缺表确认是否准备数据；若 marker/服务器身份不符则拒绝重置与停止，必须查明原因，不能删除 marker 或改成用户数据库来绕过。首次启动中途失败会尝试只停止刚分配目录，异常保留，后续先查 status 和日志，不对旧目录再 initdb。若健康检查也无法完成，控制脚本宁可拒绝；不要用 killall 兜底。

暂停时保存目录、root、最后成功命令、测试结果、失败错误码和下次第一步。/tmp 自动清理后应从全新解压目录开始；不要拿无 marker 的旧数据冒充新集群。

## 边界与官方来源

正常停启持久性不是灾难恢复。本实验没做生产备份/恢复、断电、提交时断网、Serializable 全矩阵、真实死锁、认证、权限、连接池或容量压测。后续 ORM 应保留约束名称/类型和失败测试；updated_at 不自动更新；至少一个负责人和创建者的项目权限不是外键保证的。

下列官方来源核验于 2026-09-28。psycopg 文档站当次 403，读取同官方仓库 3.3.6 标签的文档源码；PostgreSQL 文档与 18.6 发布页可读取。

- https://www.postgresql.org/docs/18/tutorial-transactions.html
- https://www.postgresql.org/docs/18/transaction-iso.html
- https://www.postgresql.org/docs/18/explicit-locking.html
- https://www.postgresql.org/docs/18/ddl-constraints.html
- https://www.postgresql.org/docs/18/errcodes-appendix.html
- https://github.com/psycopg/psycopg/blob/3.3.6/docs/basic/transactions.rst
- https://www.postgresql.org/docs/release/18.6/
