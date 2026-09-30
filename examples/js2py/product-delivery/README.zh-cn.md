# 产品交付模板

这些文件是把 V4 产品接入真实目标环境的中立模板。它们不是已部署应用，也不能替代学习者自己的 S03 授权、数据库模型、迁移或 O04—O06 运维证据。

## 使用顺序

1. 先把空白的 `starter/` 目录复制为自己的产品仓库；之后再把审查过的运维文件复制到 `ops/` 与 `.github/workflows/`。
2. 替换 `app`、`migrations`、健康路由、镜像、域名、服务账户、数据库服务名和秘密引用。
3. 按官方文档核对目标 Docker Engine、Linux/systemd、Caddy、PostgreSQL、CI 和秘密存储版本。
4. 在一次性 PostgreSQL 服务上运行验证作业。
5. 在获批目标中执行审查过的迁移，启动应用，验证真实 HTTPS，并运行已认证/越权冒烟场景。
6. 受邀使用前演练备份、隔离恢复、应用回退和会话/成员失效。

文件不包含凭证。`product.service.template` 是 Compose 路径之外的 systemd 替代方案；同一目标只选择一种进程监督方式。`commands/release.sh` 在缺少不可变 app/Caddy 摘要、V0—V3 全部通过的格式有效整合记录、已通过的构建、迁移、备份恢复和回退证据、人工批准、备份政策或回退责任人时会拒绝执行。它也不会因此认证后端或公网运营。`commands/restore.sh` 只接受全新的 `restore_` 数据库名，不提供覆盖或 `--clean` 回退。

CI 的 `release` 作业会故意失败，直到学习者实现并审查 `ops/deploy-approved.sh`。验证作业变绿不是部署批准。备份和恢复脚本要求审查过的 `pg_service.conf` 与受保护 passfile；不要把密码写进服务文件、命令参数或仓库变量。

## 文件说明

- `starter/`：故意空白的 V0 产品目录，不包含实现和锁文件。
- `Dockerfile`、`.dockerignore`、`compose.production.yaml`：镜像、构建上下文、网络、秘密、卷和进程边界。
- `Caddyfile.template`：同主机/容器反向代理起点。
- `product.service.template`：Linux/systemd 替代入口。
- `.github/workflows/verify-and-release.yml.template`：一次性 CI 数据库、锁定验证、环境审批和显式部署适配门槛。
- `commands/release.sh`：目标发布骨架。
- `commands/backup.sh`、`commands/restore.sh`、`pg_service.conf.template`：受控备份与隔离恢复骨架。
- `app/secret_config.py`、`app/healthcheck.py`：必须接入学习者真实应用的应用适配器。
- `product-workbook.zh-cn.md`：把章节实验转成自己产品的分阶段工作包。


这里使用的官方机制包括 [uv Docker 集成](https://docs.astral.sh/uv/guides/integration/docker/)、[Docker 构建最佳实践](https://docs.docker.com/build/building/best-practices/)、[Caddy 自动 HTTPS](https://caddyserver.com/docs/automatic-https)、[GitHub Actions 环境](https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments)和 [PostgreSQL pg_restore](https://www.postgresql.org/docs/18/app-pgrestore.html)。
## 贯穿整合证据记录

`templates/integration-record.json` 用读者声明的方式记录 V0—V5。复制到自己的产品仓库，替换占位产品身份，并随进度更新阶段与证据状态。

在解压后的目录运行格式检查器：

```bash
python3 check_integration_record.py templates/integration-record.json
```

检查器只验证字段形状、阶段/证据一致性、相对 artifact 引用、UTC 时间戳和明显的嵌入凭证。它不会打开引用文件、执行测试、检查后端、证明脱敏、授予毕业或批准公网运营。通过格式检查的记录仍需 artifact 与人工审查。
- `templates/product-contract.md`：V0 产品合同模板。
- `templates/integration-record.json`：V0—V5 证据声明；检查器只验证格式。
- `templates/incident-record.template`：事故与修复记录。
- `templates/maintenance-record.template`：可复用维护证据记录。
- `check_integration_record.py`：格式检查器；不执行产品，也不批准发布。
