# s02-authorization：完整独立本地实验

[English](README.md) · [繁體中文](README.zh-tw.md)

## 1. 契约与起点

这是教材 S02 的独立下载包，不从别章导入源码，不需要前端依赖。读者已学 D06 的 PostgreSQL、事务、迁移与 fixture；S02 还依赖 S01 身份机制，S03 还依赖 S02 对象权限。先根据本 README 预测结果，再用真实 HTTP 和数据库验证；编译成功不算 API 验收。完整机制与折叠答案见对应教材章节。

所有实验只监听 127.0.0.1；PostgreSQL 只使用本程序的私有 Unix socket。**不得将实验直接暴露公网，不得连接或停止用户现有数据库。** 本地 trust 依赖私有目录与本机用户边界，不代表生产数据库认证设计。

基线核验 **2026-09-28**：CPython 3.13.15、uv 0.12.13、FastAPI 0.135.1、Uvicorn 0.42.0、Pydantic 2.12.5、SQLAlchemy 2.0.54、Alembic 1.20.0、psycopg[binary] 3.3.6、PostgreSQL 18.6、argon2-cffi 25.1.0、pytest 8.4.2。公开 PyPI 的 uv.lock 固定实际依赖，不宣称最新；Python 范围 >=3.13,<3.14，uv 不将实验作为发布包安装。

## 2. 文件职责

| 文件 | 职责 |
| --- | --- |
| pyproject.toml / uv.lock / .python-version | 声明、完整解析与解释器 pin |
| migrations / alembic.ini | 从空库到本章的真实迁移；001–003 完整沿用 D |
| models.py / schemas.py | 数据库存储与请求/公开模型分开 |
| db.py / security.py | 每请求事务入口、Argon2id、会话查验/撤销；不是全局 Session |
| app.py / serve.py | HTTP 适配、错误脱敏与只监听回环的进程入口 |
| admin.py / client.py | 受控开通与 getpass 客户端；不打印密码/Bearer |
| labdb.py | 自建、核对归属、重启/停止独占临时 PG 集群 |
| tests / solutions | 真实 PG/HTTP 验收和独立变式答案 |
| SOURCES.md / VERIFICATION.md | 官方核验与实际证据/未覆盖面 |

## 3. 工作目录与首次启动

在解压后的 `s02-authorization` 根目录操作；仓库中对应 `examples/js2py/s02-authorization`。确认本机可调用 PostgreSQL 18.6 的 postgres、initdb、pg_ctl；本轮位于 /opt/homebrew/bin。不要用已有服务作为替代。

```bash
export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
export UV_PYTHON_INSTALL_DIR=/tmp/langshift-js2py-python-20260928
export UV_CACHE_DIR=/tmp/langshift-js2py-uv-cache-20260928
unset VIRTUAL_ENV UV_PROJECT_ENVIRONMENT UV_ACTIVE UV_PYTHON UV_CONFIG_FILE
export UV_NO_CONFIG=true
uv --version
uv sync --locked
uv run --locked python --version
uv run --locked python labdb.py start
```

预期 uv 0.12.13、Python 3.13.15。labdb.py 创建模式 0700 的 mkdtemp 目录、模式 0600 的归属标记与 .lab-state.json，启动无 TCP 监听的 PG。**将它打印的 DATABASE_URL export 行复制到本终端**；该 URL 是私有 socket 地址，不含密码。isolation.py 在连接前删除所有隐式 PG* 配置，子命令也排除 PGHOSTADDR/PGSERVICE 等 libpq 环境干扰。别把任意已有 DATABASE_URL 继续带入实验。然后执行：

```bash
uv run --locked alembic upgrade head
uv run --locked alembic current
uv run --locked python admin.py create-user Alice
uv run --locked python admin.py create-user Bob
uv run --locked python serve.py --port 8062
```

current 必须为 005_owner_guard。旧 D 用户经 004 迁移后保持停用、没有默认密码，需明确开通。create-user 拒绝覆盖已经设置的密码。新密码 15–128 字符，只在 getpass 提示中输入并确认，不放在参数、日志、环境默认值或教程常量里。禁止盲目 stamp；安全 downgrade 故意不自动删除历史。

/health/live 只检查进程；/health/ready 检查 DB 可用及精确迁移版本，不检查所有数据不变量。另开终端进入同目录，客户端不需要 DATABASE_URL。HTTP 端口若冲突，保留已有进程，停止自己启动失败的命令或换一个空闲端口，并在所有客户端命令中同步替换；不要按进程名批量 kill。

## 4. 身份、API 与字段契约

所有包都提供 POST /auth/token、GET /users/me、POST /users/me/password、POST /auth/logout 与 /auth/logout-all。密码是 JSON 请求体里的秘密，但只通过客户端专用提示命令输入。登录返回的随机 Bearer 只在客户端私有 .session*.json 保存，模式 0600；不 cat、不截图、不提交。客户端用 `ProxyHandler({})` 显式禁用环境代理、拒绝重定向，登录响应设 no-store；只写回环 URL 并不能绕开继承的代理。这个终端文件不是浏览器 localStorage 建议。

Argon2id 由成熟 argon2-cffi 实现，随机盐、m=65536 KiB/t=3/p=4；令牌由 secrets.token_urlsafe(32) 生成，DB 仅存 SHA-256 摘要、expiry、auth_version。普通请求重新查启用/撤销/过期/版本，不能只看登录时成功。改密与 logout-all 提升版本；disable/enable 均提升版本，所以旧令牌不会复活。用户共享锁与撤权排他锁定义顺序：既有操作可以完成，撤权提交后的新操作被拒绝，不追回已开始响应。

S02/S03 另有项目 POST/GET 列表、项目 GET/PATCH/DELETE、成员 GET/POST/DELETE、项目内任务 POST/GET 列表及任务 GET/PATCH/DELETE。列表 limit 默认20、范围1–100；offset 默认0且非负，id 升序，total 仅当前作用域。项目 name 非空白；任务 title 非空白保留原字形，description 可空、status 为 todo/doing/done、minutes 严格非负 int、priority 0–2、due_at 可空但非空时必须带时间偏移。id/project_id/created_by 由服务管理；不支持 done/note 别名或客户端自授 role。成员邀请的 user_id 仅表示目标用户。

非成员/不可见对象 404；当前成员没有操作权限 403。成员可以读、创建任务，只能改删自己创建的任务；owner 可改删项目内任务并管理项目/成员，但删除 owner 关系为 409。项目+owner 同事务；部分唯一索引只保证“至多一位”。项目写/成员移除锁定义先后，全局项目列表只有成员过滤的语句快照，无 items/total 同快照承诺。

## 5. 真实客户端验收

```bash
uv run --locked python client.py --port 8062 --session .session-alice.json login Alice
uv run --locked python client.py --port 8062 --session .session-bob.json login Bob
uv run --locked python client.py --port 8062 --session .session-alice.json request GET /users/me
uv run --locked python client.py --port 8062 --session .session-bob.json request GET /users/me
```

```bash
uv run --locked python client.py --port 8062 --session .session-bob.json request POST /projects --json '{"name":"Bob private"}'
uv run --locked python client.py --port 8062 --session .session-bob.json request POST /projects/1/tasks --json '{"title":"Bob task","minutes":25}'
uv run --locked python client.py --port 8062 --session .session-alice.json request GET /projects
uv run --locked python client.py --port 8062 --session .session-alice.json request GET /projects/1
uv run --locked python client.py --port 8062 --session .session-alice.json request PATCH /projects/1/tasks/1 --json '{"status":"done"}'
```

```bash
uv run --locked python client.py --port 8062 --session .session-bob.json request POST /projects/1/members --json '{"user_id":1}'
uv run --locked python client.py --port 8062 --session .session-alice.json request GET /projects/1/tasks/1
uv run --locked python client.py --port 8062 --session .session-alice.json request PATCH /projects/1/tasks/1 --json '{"status":"done"}'
uv run --locked python client.py --port 8062 --session .session-alice.json request POST /projects/1/tasks --json '{"title":"Alice task","created_by":2}'
```

```bash
uv run --locked python client.py --port 8062 --session .session-bob.json request DELETE /projects/1/members/2
uv run --locked python client.py --port 8062 --session .session-bob.json request DELETE /projects/1/members/1
uv run --locked python client.py --port 8062 --session .session-alice.json request GET /users/me
uv run --locked python client.py --port 8062 --session .session-alice.json request GET /projects/1
```

这些命令假设新库 Alice=1、Bob=2、首项目/任务=1；以真实响应替换。Bob 创建201/201，Alice 列表200但不含项目、直接读/改404；邀请后可读200，但改Bob任务403，伪造created_by为422。拒删owner409，移除Alice204，其me200而项目404。恢复由Bob重新邀请；重复邀请409后合法请求仍应成功。不要只验正常路径。

## 6. 自动验收与失败恢复

```bash
uv run --locked python -m pytest -q
```

当前 43 个用例。fixture 忽略外部 DATABASE_URL，为自己创建 PG18.6、迁移、启动真实 Uvicorn，标准库客户端发实际 HTTP；每例仅清理自己库中的声明表。它运行 solutions 扩展入口并复验基础路由，覆盖独立变式。输出案例数和脱敏证据见 VERIFICATION.md。维护者设置 SECURITY_EVIDENCE_DIR 可保存脱敏 HTTP/两连接观察；这不是生产审计日志。

| 失败 | 观察与恢复 |
| --- | --- |
| 缺/错 DATABASE_URL | 不输出实际连接字符串；重新复制本实验 labdb.py status 的 export |
| ready503、live200 | 核查自有PG状态和迁移版本；修复后ready200，不跳过迁移 |
| 错误/过期/篡改Bearer | 通用401；用专用客户端重新登录，不改数据库绕过验证 |
| 密码/JSON/extra字段不合法 | 422仅loc/type，不回显input/ctx/msg或秘密字段名；修正输入 |
| 真实数据库操作错误 | 泛化409或503；事务回滚，恢复schema后后续请求成功；不输出SQL驱动细节 |
| 临时服务端口被占 | 不杀已有进程；只更改自己的服务/客户端端口 |

测试真的令会话过期、破坏Bearer字符、停用/启用、改密、重启API及自有PG，并检查敏感字段、额外键、破损JSON的输出与应用/PG日志。S02/S03还检查body/query/path输入；并发撤权有不同backend PID和pg_blocking_pids证据。它不证明每个未知异常、第三方日志、代理或APM都已脱敏；未来新增路径需独立安全审查。

客户端隔离回归仅用自有回环监听器和合成凭证：代理环境有值、no_proxy不存在，目标收到3个请求、代理0个、重定向目标0个。另一helper测试注入无效PGHOSTADDR/PGSERVICE/PGUSER/PGDATABASE/PGPASSWORD后，仍成功启动、重启并删除自己的socket-only集群。

维护者从干净副本复跑时，仓库runner支持 `--lab-root /path/to/extracted-lab` 或 `JS2PY_LAB_ROOT`（也可指定包含同名实验目录的父目录）。它清除继承的VIRTUAL_ENV、UV_PROJECT_ENVIRONMENT、UV_ACTIVE、UV_PYTHON及其余UV配置重定向，设置UV_NO_CONFIG、命令行固定Python，只保留明确UV_PYTHON_INSTALL_DIR/UV_CACHE_DIR存储路径；还排除PG*及pytest插件/参数覆盖。默认源码复跑也只使用该实验自己的.venv，并拒绝环境符号链接。

## 7. 独立重建与变式
只带身份、迁移与环境，从权限矩阵重建对象服务，不导入参考authorization.py。先让Alice拿到Bob真实ID验越权，再验CRUD和原子owner创建。统计变式只算本项目未完成任务：todo/0、doing/15、done/40得count2/minutes15，外人404，不受列表分页影响。先写自己的版本，再看 solutions/project_summary.py。
```bash
uv run --locked python serve.py --port 8062 --app solutions.project_summary:app
uv run --locked python client.py --port 8062 --session .session-bob.json request GET /projects/1/summary
```

## 8. 暂停、恢复与最终清理

先在拥有API的终端Ctrl-C。保留数据时运行labdb.py status，保存不含秘密的状态记录，下次复制它打印的export，再启动API。需要证明数据库持久化时用restart；不要用stop后数据消失来声称持久化失败。

```bash
uv run --locked python labdb.py status
uv run --locked python labdb.py restart
```

API重启/PG重启后，仍在有效期且未撤销的会话/已提交记录应保留。会话仍可能因正常TTL到期而401；这不是丢库。完整结束时，先停API，再执行：

```bash
uv run --locked python labdb.py stop
```

**stop确认归属和进程退出后会删除整个临时PG数据目录。** 只清理自己创建的私有.session文件，不用全盘通配符，不杀用户DB。

```text
checkpoint: s02-authorization
migration: 005_owner_guard
last_result: record status and non-secret object IDs only
credential_values: never recorded
api: stopped in owning terminal
postgres: retained for resume OR explicitly deleted by owned helper
next: status, export, migrate if needed, serve, fresh login if expired
```

## 9. 打包与未验证边界

同级 `s02-authorization-files.json` 是正向allowlist；打包只读取其中路径，不递归整个实验目录。排除 .venv、__pycache__、.pytest_cache、.env*、.lab-state.json、.session*（含中断留下的.new）、PGdata/socket、日志、凭证和临时证据。文件列表由集成方打包；本包不捆绑运行环境或数据库。

未验证：生产TLS、限流/容量、请求体大小、泄露密码筛查、找回/MFA、外部日志/APM、任意未知异常、时钟偏差、备份恢复、RLS、跨服务副作用和所有锁交错。全局列表/已开始响应不能追溯撤权；邀请目标并发被禁用不构成原子开通保证。S03也不承诺清理后永久去重、恰好一次或无条件自动重试。测试通过不等于安全审计通过，主线将按最终文件hash独立审查。
