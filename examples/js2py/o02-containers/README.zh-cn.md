# O02 容器与可部署应用

前置 O01/L08。这是 health-only smoke app，不含任务、认证、授权或数据库；不能接真实用户。Dockerfile/Compose/安全runner 完整提供，但本机没有容器引擎，真实构建/运行仍待验收。

## 环境与恢复

核验日期：**2026-09-28**。需要普通 POSIX 账户；不以 root 运行权限实验。CPython **3.13.15**、uv **0.12.13**、pytest **8.4.2**。`.python-version` 选解释器，pyproject 声明 `>=3.13,<3.14`，uv.lock 锁依赖；`[tool.uv] package=false` 表示不打包这个练习为可发布 Python 包。

Web 基线：FastAPI **0.135.1**、Uvicorn **0.42.0**、Pydantic **2.12.5**、HTTPX **0.28.1**、Starlette **0.52.1**、AnyIO **4.12.1**；没有前端依赖。

仓库用户从仓库根目录执行下列 cd；ZIP 用户直接进入解压后的同名实验根目录，里面应有 pyproject.toml。`--locked` 拒绝悄悄更新锁。

```bash
cd examples/js2py/o02-containers
pwd
uv --version
uv sync --locked
uv run --locked python --version
```

维护者锁文件已用 `uv lock --default-index https://pypi.org/simple` 实际生成。读者恢复不需要重新解析。环境与缓存不进清单/ZIP，所有数据实验用自己创建的临时目录。

## 本地可实际执行

local_probe.py 启动自己持有的 loopback Uvicorn 子进程；目录不可写时 live 保持200而 ready变503，恢复后ready200；/tasks404。check_config 只检查选定不变量，不是 Docker/Compose 完整解析器。secret_demo 仅处理虚构标记且不输出值。

```bash
uv run --locked python check_config.py
uv run --locked python local_probe.py
uv run --locked python secret_demo.py
uv run --locked python -m pytest -q
uv run --locked python -m pytest -q solutions/test_restore_copy.py
uv run --locked python container_probe.py
```

```text
host_http_live=200
host_http_ready=200
unwritable_live=200
unwritable_ready=503
restored_ready=200
tasks_not_implemented=404
container_runtime=NOT_VERIFIED
```

container_probe 无显式 opt-in 时 exit77，报告 environment_pending，不能计为容器通过。pytest 标准14、独立3已实跑。普通文件恢复与真实容器卷验证是两个层次。

## 构建与运行边界

Dockerfile 两阶段恢复锁定生产依赖，运行用户10001；.dockerignore先拒绝再明确放行九个文件。compose.json 需显式 -f，宿主发布127.0.0.1:8033，容器内部监听0.0.0.0:8000；两个网络命名空间不能混淆。只读根、/data命名卷、/tmp临时空间与最小权限分别指定。healthcheck报告就绪，并不会自动完成授权或因unhealthy而重启。

普通OPS_DATA_DIR不是秘密。密码/token不得写入镜像层、ARG/ENV、命令行、日志或下载包；secret_demo不是生产秘密管理器。基础镜像tag可用性/digest/架构未在引擎实测。卷不是备份；同容器stop/start保留可写层，删除重建才不自动保留它。

## 用户自备受控引擎后的命令（未实跑）

先审读container_probe.py。需要Linux Docker Engine>=28、本地UNIX socket、镜像下载许可。不要填远端TCP/SSH，也不使用默认context。程序清除Docker环境选择并使用空临时配置，避免读取凭证助手；资源名随机且只移除自己创建的容器/卷/镜像，不全局prune。基础镜像/构建缓存可能保留。实际输出必须由你的目标环境产生。

```bash
uv run --locked python container_probe.py --socket /path/to/controlled/docker.sock --confirm-controlled-engine
```

runner 验证 UID、只读根、host绑定、健康、带卷重建=1、无卷同实例stop/start=1、无卷重建=0。端口冲突不要kill用户进程；权限失败不要把真实数据目录chmod777。构建失败应保留阶段信息，不能改latest绕开版本约定。

## 独立需求

把停止写入的教学counter复制到新空目录并读回一致值；拒绝非空目标、拒绝损坏源且不改原状态。solutions/restore_copy.py和三个测试是参考；不能用普通文件拷贝冒充活跃PostgreSQL备份。

## 环境矩阵（机器可读版本：ENVIRONMENT.json）

| 状态 | 证据与门槛 |
| --- | --- |
| 已实际运行 | 配置文件选定不变量、真实loopback HTTP200/503/恢复/404、普通账户权限失败、虚构0600秘密标记、普通文件恢复；没有显式许可时runner返回77。 |
| 本机不可运行 | 没有发现Docker/OrbStack/Podman/Apple container等CLI、常见应用或socket；没有受控Linux容器引擎。 |
| 用户需自备 | 受控本地Linux Docker Engine>=28、核实过的UNIX socket、镜像下载/构建的网络、存储和许可；不使用远端context。 |
| 待环境验收 | 实际基础镜像tag/digest/架构与构建、Compose解析、UID10001/read-only/loopback发布、卷owner/健康/启停/删除重建、引擎runner分支与清理。完整capstone/授权/数据库另行集成。 |

本轮标准 **14**、独立 **3** 个测试通过。源码与文稿 `implemented`；矩阵中的外部环境 `environment_pending`，不是整体部署通过。普通 macOS 测试不能代替 Linux/容器/公网或 Windows 证据。

## 恢复学习与排错记录

记录源码/锁摘要、cwd、工具版本、最后成功命令、失败阶段与分类、实际测试数、环境矩阵和下次第一步。不要记录完整环境、真实 token、数据库 URL 或私钥。恢复先 `uv sync --locked`，再跑标准与自己写的独立测试。只有参考答案通过，不代表你能独立实现。

## 一手资料

SOURCES.json 保存 2026-09-28 核验的官方地址、作用范围、HTTP获取结果与SHA-256摘要。章节正文解释每个机制，README 提供离线运行入口。这里没有自动创建生产资源、安装系统软件或接受服务条款。
