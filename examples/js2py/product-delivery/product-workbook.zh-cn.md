# js2py 产品工作包：把章节实验变成自己的服务

这不是实现答案，也不是按周推进的计划。你按能力阶段工作；可以暂停、恢复、查官方文档，但每个阶段必须在自己的产品仓库留下可复核证据。

先把 `templates/integration-record.json` 复制到自己的仓库。每完成一项证据，更新对应状态；中断时更新 `next_action` 和产品提交。格式检查器只检查记录形状，不执行产品。

## V0：自己的 Python 产品基础

进入条件：已完成 L10，并能在第二个空目录恢复本地程序。

先复制本交付包中的空白 `starter/` 目录。把 `templates/product-contract.md` 和 `templates/integration-record.json` 复制到自己的 `docs/`，再生成自己的 `uv.lock`。

你要自己写：

- `pyproject.toml` 与 `uv.lock`；
- 业务规则模块；
- 输入校验；
- 文件读写边界；
- 普通业务测试；
- 一页产品契约：任务字段、合法值、缺失值、重复标题、状态变化。

不能把 L10 下载包或折叠答案整体复制为产品。参考答案只在独立尝试后用来核对职责。

离开证据：

- `environment_recovery`：第二个空目录恢复并运行；
- `business_tests`：空集合、零值、非法输入、重复标题、输入不变；
- `failure_recovery`：坏 JSON 或编码错误不覆盖旧数据，修复后重跑。

## V1：把同一业务暴露为 HTTP

进入条件：V0 通过，且能解释每个路由会改变什么状态。

你要自己写：

- FastAPI 应用入口；
- 请求与响应模型；
- 路由组织；
- 配置读取；
- TestClient 测试；
- 真实 Uvicorn 请求记录；
- 最小浏览器或 HTTP 客户端联调记录。

内存存储可以存在，但运行文档必须写明重启丢数据，且不能称为上线版本。

离开证据：

- `http_contract`：方法、状态码、字段、错误形状；
- `api_tests`：成功、422、404、PATCH 三态、输出过滤；
- `real_process_requests`：真实端口上的请求与清理记录。

## V2：把状态放进 PostgreSQL

进入条件：V1 通过，且能解释内存状态为什么不能满足重启和并发。

你要自己写：

- users/projects/project_members/tasks 关系设计；
- SQLAlchemy 模型；
- Alembic 迁移；
- 每请求 Session 与事务边界；
- 隔离数据库测试；
- API 存储替换后的回归。

不要用 `create_all` 代替迁移，也不要删库重建解决已有数据变化。

离开证据：

- `empty_database_migration`：空库升级；
- `existing_data_migration`：已有数据升级并核对；
- `transaction_failure_recovery`：两步写入第二步失败后无残留；
- `isolated_database_tests`：测试库可重复清理。

## V3：登录、对象授权与幂等

进入条件：V2 通过，且数据库与应用版本兼容记录存在。

你要自己写：

- 受控开户命令；
- Argon2id 密码哈希；
- 不透明 Bearer 会话；
- 会话摘要、过期、撤销和认证版本；
- 每请求身份重建；
- 项目成员作用域查询；
- 对象级授权；
- 创建任务幂等回执。

请求体不能自报 `user_id`、角色或创建者。前端隐藏按钮和 CORS 不是授权。

离开证据：

- `identity_lifecycle`：登录、改密、停用、退出全部会话；
- `object_authorization_negative`：Alice 知道 Bob ID 也无法读写；
- `revocation`：移除成员后旧凭证失去对象权限；
- `idempotency_and_retry`：同 key 同内容重放、异内容冲突、真实竞争。

## V3.5：只在需要处加入异步

进入条件：V3 通过，且有一个真实可选外部依赖需求。

你要自己写：

- 外部适配器；
- 共享客户端生命周期；
- 总预算和阶段超时；
- 有界并发；
- 响应验证；
- 取消清理；
- 故障替身测试。

核心 CRUD 不依赖外部服务成功。不要把 `BackgroundTasks` 或内存队列称为持久任务系统。

离开证据：

- `external_failure_isolation`：外部失败不影响任务读写；
- `cancellation_cleanup`：取消后无任务或客户端泄漏；
- `core_crud_regression`：核心 CRUD 回归仍通过。

## V4：真实目标环境发布与维护

进入条件：V3/V3.5 通过，且你已获准使用目标主机、域名、证书、秘密存储、数据库、CI 和通知渠道。

你要自己接入：

- Docker 或 systemd 运行入口；
- 迁移身份与应用身份；
- Caddy 或等价 HTTPS 入口；
- 托管 CI；
- 日志、关联 ID 和告警；
- 备份、隔离恢复、回退手册；
- 受邀试用范围和维护责任人。

本地 O 阶段实验证明机制，不证明你的产品可上线。

离开证据：

- `build_identity`：固定提交和镜像摘要或制品标识；
- `controlled_migration`：真实目标迁移命令与版本；
- `public_https`：外部 DNS、证书链和真实 HTTPS 请求；
- `logs_and_delivered_alert`：一次故障定位和实际送达通知；
- `backup_and_isolated_restore`：备份、恢复、数据/权限验证；
- `compatible_rollback`：有数据回退或安全冻结证据；
- `invited_use_approval`：范围、批准人和维护责任。

## V5：独立新需求

进入条件：V4 已通过，且你已阅读 G01 场景目录。

你要自己完成 G01 的任务评论需求：

- 关系与接口设计；
- 迁移；
- 权限；
- 并发与重复请求；
- 发布回退；
- 恢复验证；
- 人工评阅。

离开证据：

- `independent_feature`；
- `feature_release_and_rollback`；
- `feature_restore`；
- `human_review`。

## 暂停与恢复

每次暂停记录：

- 当前阶段；
- 产品提交；
- schema 版本；
- 最后成功命令；
- 实际失败；
- 已清理的进程；
- 未验证门槛；
- 下一个具体动作。

恢复时先复现上一次可运行状态，再继续。不要因为间断重装一切，也不要为了推进而删除失败证据。

## 维护证据记录

每处理依赖/安全更新、证书续期、备份或恢复、事故、权限变更、用户反馈跟进、容量/成本审查，都使用 `templates/maintenance-record.template` 保存一条记录。记录责任人、产品/schema 版本、已核对官方资料、动作、测试、备份恢复证据、通知送达证据、回退兼容性、未解决风险和下次审查触发条件。
