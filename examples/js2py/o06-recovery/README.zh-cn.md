# 恢复验收与受控开放 — o06-recovery

完整独立本地实验。先读 O04/O05/O06 对应正文，不导入其他章节目录。
旁边 `o06-recovery-files.json` 是网页与下载的明确 allowlist，不能递归压缩当前工作目录。

## 实测环境与命令

日期 2026-09-28。CPython3.13.15、uv0.12.13、pytest8.4.2、FastAPI0.135.1、
Uvicorn0.42.0、Pydantic2.12.5、HTTPX0.28.1、SQLAlchemy2.0.54、Alembic1.20.0、
psycopg[binary]3.3.6、PostgreSQL18.6、Argon2-cffi25.1.0。Starlette0.52.1、
AnyIO4.12.1 固定兼容；requires-python 为 >=3.13,<3.14，uv package=false。
真实锁来自 public PyPI，包含制品哈希。

在解压目录运行。postgres/initdb/pg_ctl/psql/pg_dump/pg_restore 必须事先存在于
/opt/homebrew/bin 或指定 PG_BIN 目录。本实验不安装系统服务器；错误版本会在
修改数据库前拒绝。其他操作系统需另行运行验证，不用 macOS 结果冒充 Linux。

仓库总 runner 为子进程重建环境：丢弃继承的 `UV_*`、虚拟环境选择与 Python 注入设置，再固定课程 cache/Python 安装目录、public PyPI 和 `UV_NO_CONFIG=1`；`PG*` 也只保留 `PG_BIN`。实测使用自己创建的“外部虚拟环境”诱饵、错误解释器路径和无效用户 uv 配置，确认安装只发生在当前干净副本的 `.venv`，诱饵目录内容不变。不要把这些防护误解为能修复已经在脚本启动前运行的外层 uv：手动执行下方 uv 命令前，应退出其他虚拟环境并使用干净终端；清除 `VIRTUAL_ENV`、`UV_PROJECT_ENVIRONMENT`、`UV_ACTIVE`、`UV_PYTHON`、`UV_CONFIG_FILE` 等覆盖项，并设置 `UV_NO_CONFIG=1`。若直接 Python 入口拒绝 PG 变量，只在本次实验环境中移除它报告的名字，不修改生产配置、更不打印其值。

```bash
uv sync --locked
uv run --locked python ci.py
uv run --locked python -m pytest -q solutions
uv run --locked python demo.py
```

ci.py 检查语法、运行 6 项正常测试与真实进程/数据库演练；独立答案另有
1 项测试。ci.py 已包含 demo，单独 demo 用全新集群重放。稳定 PASS 行
代表已检查阶段；耗时是测量值而非固定输出。语法、mock 决策、检查 YAML 都不
代替实际运行。

## 本章实际证明的内容

其中三项恢复专项使用真实 PostgreSQL，分别验证实际导入、损坏拒绝与目标不可覆盖。演练生成 custom pg_dump，
检查目录与哈希，恢复到全新隔离库，比较全部表内容指纹，再测约束、identity
序列和运行角色权限。截断副本既被校验和拒绝，也实际触发 pg_restore 失败；
坏目标没有用户表。只有 .dump 文件或能列目录绝不算恢复通过。

快照可能复活已撤销 token 或旧成员关系。开放运行角色 CONNECT 之前，先停用
恢复账户、递增 auth_version、删除会话，再核对合成的备份后安全变更记录，
仅明确批准测试账户。真实 HTTP 验证旧/过期 token 和跨用户读取被拒绝。
真实环境缺少权威较新安全记录时保持账户停用、目标隔离，不能把旧备份当现状。

源库保留一条刻意在快照后提交、恢复库没有的任务。MEASURED 仅报告本次快照
年龄与恢复加验收耗时，不是生产 RPO/RTO。pg_dump 不自动覆盖角色/全局对象、
配置/密钥/外部文件。源与目标在同一自有宿主；未验证跨机容灾、定时/加密/
异地保留或 PITR。合成归档放在 0700 目录下、模式 0600，退出删除。
独立清单门禁不能替代真实恢复。

## 环境边界与端口所有权

传入私有 socket 的 host 还不够：libpq 仍可能从 `PGHOSTADDR`、`PGSERVICE`、`PGSERVICEFILE` 等环境变量取得另一个连接默认值。`reject_connection_environment` 在创建临时目录之前，以及每次直接连接、迁移和服务启动之前，拒绝继承的全部 `PG*` 变量，唯一例外是只定位可执行文件的 `PG_BIN`。错误只列变量名，不打印值，也不修改调用者环境。Python 连接、SQLAlchemy 的连接创建器和 PG 子命令都使用自有目录内的空白 0600 `empty.pgpass`，不读取用户的默认密码文件。直接运行 `demo.py` 或 `ci.py` 也执行这些防护，不依赖仓库总 runner 先替它清理。

启动 API 不再先探测空闲端口、关闭探测 socket，再要求另一个进程抢占同一号码。Uvicorn 自己用 `--port 0` 完成绑定；控制器从**该子进程自己的私有启动日志**读取实际端口，再请求 readiness。`--no-access-log` 不关闭 info 级启动 banner；控制器固定无颜色日志和单 worker。两个同版本服务也使用不同日志文件。测试实际同时启动两个服务，核对两个不同端口、各自 banner、真实请求和退出清理。这消除了选端口后释放再绑定的窗口，不是对任意并发故障的保证；未来 Uvicorn 改变 banner 格式时会超时拒绝，不猜测端口。

`tests/test_environment.py` 提供 3 项补充验收：继承 PG 默认值在分配/连接前被拒绝，`PG_BIN` 与自有空密码文件保持明确边界，以及两个真实服务各自绑定端口 0、通过 HTTP 后完整退出。PG 变量矩阵是一项测试里的多组断言，不夸大成多项 pytest 用例。

## 安全、身份与完整源码

ops/cluster.py 只创建自己的 mkdtemp /tmp/ls-ops-* 集群；停止/删除前核对 UID、
0700、所有权随机标记与 symlink，不接受环境里的 DATABASE_URL，不管理用户
已有 PostgreSQL。数据库只使用私有 0700 Unix socket 的本地 trust，不监听 TCP；
这是短命教学政策，不是生产认证。同一个操作系统账户仍然是信任边界。
API 只绑定 127.0.0.1 的自有临时端口。

ops/app.py 是受保护项目的运维切片，不是完整 capstone。保留 D/S status/
description/priority 字段，不沿用 H done/note；每请求检查 opaque Bearer
摘要/expiry/revoked/active/auth_version，无权限的项目 404。操作员 fixture
建立合成用户、会话和非空幂等回执，不提供公开登录/开户后门；真实上线前仍需
整合完整 S03 应用。

SQL001..006 独立复现 D/S 合同快照，007 添加可空 projects.description。
它们只用于自有实验，不允许替换既有生产迁移历史。应用启动只做兼容检查，
绝不自动迁移。管理迁移与运行身份分离，grants.sql 列出当前实验权限，不代表已经最小授权。
迁移控制器按单操作员串行执行，不是分布式发布锁。

本实验验证的是管理／运行身份分离，以及已测试的 ALTER/DROP 被拒绝；**没有证明 DML 已按最小权限收敛**。共用的 `sql/grants.sql` 仍对 projects、project_members、tasks 授予 SELECT/INSERT/UPDATE/DELETE，并对 public 的全部序列授予 USAGE/SELECT；其中部分权限超过当前“读取／创建项目”路由的需要。真正部署前，须逐个列出路由和作业需要的表操作，收窄表／序列授权，再验证必要操作成功、未使用的 UPDATE/DELETE 等操作被拒绝。已有 DDL 拒绝测试不能代替这项审计。

ops/server.py 管理实际 Uvicorn 子进程，等待 DB-backed readiness，在 finally
只停自己的服务。正常/异常退出清理自有库目录、合成归档、私有日志和 socket；
若停止/所有权检查失败，宁可拒绝删除也不触碰别人的服务。异常中断后仅排查
本次拥有的根目录；不使用全局 killall、外部 URL 的 DROP、Docker prune 或
宽泛递归删除。这里不应出现真实凭证或真实用户数据。

## 故障与恢复

工具缺失/版本错误：修工具路径，不绕过检查。所有权拒绝：重开新实验，不把
用户目录伪装成实验。刻意的迁移/权限/损坏失败有断言和修复复验；意外非零
退出就停止门禁，不能忽略后继续发布。原始异常、URL、环境整表可能含秘密，
不要为诊断全量打印。

暂停记录工作目录、锁哈希/版本、最后阶段、真实用例数、刻意/意外故障、兼容/
恢复状态、私有日志/归档政策、进程目录清理、未验证外部门槛、下次动作。
正常退出会删临时状态，恢复时重新运行，不假定旧 socket/token 文件还在。

## 明确 pending 的外部验收

本机实跑只有 macOS arm64、PG18.6 与 loopback HTTP。没有实际 Linux/systemd、
Docker build/run、Caddy/公网代理、域名/DNS/公网 TLS、托管 CI、镜像发布、
生产迁移/切流、告警送达、定时加密/异地备份、跨机恢复、代表性压测或受邀用户
试用。这些需要独立环境与授权。不能把 YAML 当发布，把告警返回值当通知送达，
把备份文件当恢复成功。

完整 S03 认证授权、请求体边界、密码哈希容量、登录限流、可信代理/CORS/凭证
策略及 O01-O03 外部门槛仍是上线前提；不扩成公开注册。本实验不做 Git 提交/
推送、不购买基础设施、不执行真实部署。

## 打包与来源

只包含 allowlist 源码、SQL、配置、锁和文档。排除 .venv、__pycache__、
.pytest_cache、.env/.env.*、凭证、日志、归档、PG数据/socket、运行时清单。
SOURCES.md 是 2026-09-28 实时核验的一手资料。仓库可选维护脚本
scripts/test-js2py-operations-delivery.py 检查干净清单副本与真实演练，不替代
缺失的外部发布门槛。
