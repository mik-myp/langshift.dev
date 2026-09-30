# js2py 贯穿整合线：从章节实验到一份可维护产品

更新：2026-09-30。本文把 39 章的独立实验连接成一条产品交付路径。它不提供一个让读者直接复制的最终后端，而是规定每个阶段应该把什么能力带回自己的产品仓库、留下什么证据，以及怎样继续使用官方文档和已有实验。

关联：[学习路线](/Users/mikmyp/Documents/code-projects/langshift.dev/docs/js2py-learning-path.zh-cn.md)、[毕业项目规格](/Users/mikmyp/Documents/code-projects/langshift.dev/docs/js2py-capstone-spec.zh-cn.md)、[章节契约](/Users/mikmyp/Documents/code-projects/langshift.dev/docs/js2py-chapter-contracts.json)。

## 1. 学习者从什么时候开始整合

从 L00 到 L09，读者可以在章节实验目录中学习机制。完成 L10 后建立自己的产品仓库，仓库从一个纯 Python 业务模块开始，逐阶段增加 HTTP、PostgreSQL、身份、权限和运维入口。

每次整合都要满足三条规则：

- 实验目录用于观察机制；产品仓库用于保留自己的设计和失败记录。
- 参考答案只能在独立尝试和失败定位之后查看；不能把另一个实验目录直接当作产品源码。
- 一个阶段进入产品仓库后，后续阶段必须通过真实迁移、真实请求和真实失败路径验证，不保留“内存版本已经足够”的隐含替代品。

## 2. 六个产品检查点

| 检查点 | 产品仓库中必须存在 | 进入下一点的证据 |
| --- | --- | --- |
| V0 / L10 | 业务函数、文件格式、普通测试、锁定环境 | 从第二个空目录恢复；坏数据不会覆盖旧数据 |
| V1 / H01—H06 | FastAPI 路由、请求/响应模型、配置、HTTP 测试、最小前端联调 | 成功、422、404、PATCH 三态、删除和重启丢数据边界都被真实请求记录 |
| V2 / D01—D06 | PostgreSQL 表、迁移、Session、事务和数据库测试 | 空库升级、已有数据升级、第二步失败回滚、独立测试库恢复均通过 |
| V3 / S01—S03 | 用户、Argon2id 哈希、不透明会话、项目成员、对象授权、幂等回执 | Alice/Bob 负向矩阵、撤权后失效、重复请求竞争和数据库约束测试通过 |
| V3.5 / A01—A02 | 可选外部服务适配器、超时、取消、限流和故障替身 | 外部服务失败不影响核心 CRUD；取消后没有任务或资源泄漏 |
| V4 / O01—O06 | 受控启动、发布、HTTPS、日志、告警、备份、恢复和回退手册 | 在目标环境完成一次发布、一次有数据回退、一次隔离恢复和受控试用审批 |

V5/G01 是在 V4 产品上完成的新需求。它要求读者修改已有模型和迁移、增加接口和权限、补测试、执行发布回退并重做恢复验证。

## 3. 每次迁移如何保留前一阶段能力

### V0 → V1：业务规则进入 API

把 L10 的业务函数作为普通 Python 模块保留，路由只负责解析 HTTP、调用业务函数和构造响应。不要把所有规则复制进路由。为每个路由写一条“业务函数测试 + HTTP 测试”，这样可以分清 Python 逻辑错误与接口边界错误。

### V1 → V2：内存状态进入数据库

先画出旧字段与新关系，再写迁移。内存 `/tasks` 的字段不能直接假装是最终产品模型：V2 要明确项目、成员、创建者和状态的关系。每个替换过的读写路径都要保留一条真实 HTTP 回归；每条有数据迁移都要有旧数据快照和升级后断言。

### V2 → V3：数据库身份进入对象授权

登录只产生 actor，不产生对象权限。所有项目和任务路径都要重新做成员作用域查询，不能在已有 SQL 外面追加一个前端传入的 `user_id`。S01—S03 的客户端和数据库是安全边界参考；产品仓库必须重新执行自己的 URL、角色和撤权测试。

### V3 → V3.5：外部依赖保持可选

外部提示、通知或搜索属于可选路径。核心事务先完成，外部适配器再以明确的超时和幂等键运行。不要把 A02 的本地故障服务、进程内队列或 `BackgroundTasks` 直接升级成持久任务系统。

### V3.5 → V4：把产品接入运维证据

O04—O06 的脚本是运维模式和验证工具。接入自己的产品时，必须替换应用启动命令、迁移入口、健康检查、权限账户、日志路径、备份表清单和恢复后的 API 验收。只运行 O04—O06 的示例并不能证明自己的产品可发布。

## 4. 产品仓库的固定目录约定

学习者可以采用自己的布局，但必须能找到这些责任：

```text
app/                 # 路由、模型、业务服务、授权
migrations/          # 版本化结构和数据变更
tests/                # 普通、API、数据库、授权和恢复测试
ops/                  # 启动、健康、发布、日志、备份和恢复入口
docs/                 # 契约、运行、故障、回退和恢复手册
pyproject.toml
uv.lock
```

应用代码、迁移账户、测试账户和运维账户要在文档中分别说明。`README` 必须写出从空目录开始的同步、迁移、测试、启动、停止、备份和恢复命令；不能只写“运行 CI”。

## 5. 读者交付证据

每个检查点都提交一份不含凭证的记录：

```text
product_revision:
schema_revision:
environment:
last_success:
tests_passed:
failure_reproduced:
failure_recovered:
deployment_target:
backup_or_restore_evidence:
known_limit:
next_action:
```

真实公网部署还需要目标主机、域名、HTTPS、秘密存储、通知渠道、备份策略和受邀用户反馈。缺少其中一项时使用 `blocked` 或 `not_run`，不要把本地演练的预期结果填入产品证据。

## 6. 官方资料和版本策略

每次整合只引用当前产品实际使用的版本文档。Python、uv、FastAPI、Pydantic、SQLAlchemy、Alembic、PostgreSQL 和 Caddy 的 `latest` 页面只能作为入口；交付记录应保存实际版本、锁文件和核验日期。升级后重新运行对应阶段的失败路径、迁移、权限、回退和恢复测试。

官方入口： [Python 3.13 教程](https://docs.python.org/3.13/tutorial/)、[uv 锁定与同步](https://docs.astral.sh/uv/concepts/projects/sync/)、[FastAPI 测试](https://fastapi.tiangolo.com/tutorial/testing/)、[SQLAlchemy Session](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)、[Alembic 自动生成](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)、[PostgreSQL 备份恢复](https://www.postgresql.org/docs/18/backup.html)、[OWASP API 安全](https://owasp.org/projects/api-security-project)和[Caddy HTTPS](https://caddyserver.com/docs/automatic-https)。这些页面解释通用机制；产品验收仍以锁定版本和实际目标环境为准。

这条整合线让学习者拥有一份不断演进的产品，同时保留独立实验对机制的隔离。它不能代替真实读者完成实现，也不能把未执行的外部部署写成已通过。

## 7. V4 真实环境证据模板

在产品真正提供给受邀用户前，保存一份脱敏的发布记录。下面的字段必须由真实目标环境填写；本地模拟值、模板域名和预期输出不能代替它。

```text
release_revision:
schema_revision:
host_owner:
host_os_and_arch:
container_or_systemd_entry:
service_account:
domain_and_dns_evidence:
certificate_issuer_and_expiry:
secret_store_reference:
database_endpoint_and_role_boundary:
migration_command_and_result:
health_live_result:
health_ready_result:
real_https_request_result:
log_and_alert_destination:
backup_id_and_retention_policy:
isolated_restore_target:
restore_validation_result:
rollback_revision_and_compatibility:
pilot_scope:
pilot_feedback_and_followup_revision:
known_limit:
next_maintenance_action:
```

真实凭证、连接密码、私钥、完整用户数据和原始会话令牌不进入记录。记录引用经过访问控制的外部位置，并保存操作者、时间和目标版本。任何字段缺失时，发布状态保持 `blocked` 或 `not_run`，不能用本地测试结果填充。
