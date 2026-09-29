# O01 操作系统与服务进程

前置 A02 与语言/文件/依赖/测试基础。理解程序启动时的 cwd、环境、权限、端口与退出方式，再讨论容器。worker 只保存一次性启动计数；不是完整任务 API，不是可靠数据库。

## 环境与恢复

核验日期：**2026-09-28**。需要普通 POSIX 账户；不以 root 运行权限实验。CPython **3.13.15**、uv **0.12.13**、pytest **8.4.2**。`.python-version` 选解释器，pyproject 声明 `>=3.13,<3.14`，uv.lock 锁依赖；`[tool.uv] package=false` 表示不打包这个练习为可发布 Python 包。

仓库用户从仓库根目录执行下列 cd；ZIP 用户直接进入解压后的同名实验根目录，里面应有 pyproject.toml。`--locked` 拒绝悄悄更新锁。

```bash
cd examples/js2py/o01-operating-system
pwd
uv --version
uv sync --locked
uv run --locked python --version
```

维护者锁文件已用 `uv lock --default-index https://pypi.org/simple` 实际生成。读者恢复不需要重新解析。环境与缓存不进清单/ZIP，所有数据实验用自己创建的临时目录。

## 文件与实际命令

worker.py 是前台单写者，--once 只执行一次。process_lab.py 持有自己创建的子进程并验证信号；environment_lab.py 明确两个 cwd 与子进程配置；permissions_lab.py 只改临时文件；port_lab.py 只创建 loopback sockets。所有运行都有限超时/清理，不搜索或停止别人的进程。

```bash
uv run --locked python process_lab.py
uv run --locked python environment_lab.py
uv run --locked python permissions_lab.py
uv run --locked python port_lab.py
uv run --locked python -m pytest -q
uv run --locked python -m solutions.two_directories
uv run --locked python -m pytest -q solutions/test_two_directories.py
```

关键实测输出如下。负的 -9 是 POSIX subprocess 表示，不是 HTTP 状态或 shell 必然返回值。

```text
missing_config_exit=78
SIGTERM: subprocess_returncode=0 cleanup=True
SIGINT: subprocess_returncode=0 cleanup=True
SIGKILL: subprocess_returncode=-9 cleanup=False
same_directory_across_processes=2
[2, 1]
```

## 故意失败与恢复

缺少/相对 OPS_DATA_DIR →78；损坏 JSON、列表根或 bool starts →65；自有不可写目录 →74；错误 cwd →FileNotFoundError；第二次绑定同一地址被拒绝；SIGKILL 不执行清理。测试确认这些失败，不把它们转成业务成功。不要用 sudo/chmod777 掩盖权限问题。重建新的自有临时目录是本实验恢复，不代表真实数据库可丢弃。

## 手工 worker 与停止

若要手工运行，先准备只用于本实验的目录，通过 OPS_DATA_DIR 传入绝对路径，启动 worker.py；ready 后它一直等待，终端的 Ctrl+C 请求 SIGINT 正常结束。自动脚本负责清理自己的 Popen 对象，完成后不额外 kill。没有信号/超时证据前不声称所有 finally 都会执行。

## Linux/systemd（未实跑）

完整单元在 systemd/ops-worker.service。目标管理员须先确认没有同名服务或账户，在可重建 Linux 主机创建专用 langshift-ops 非登录账户/组，将源码部署到 /opt/langshift/o01-operating-system 并在目标目录恢复 .venv；服务账户能读/执行源码，不能修改它。StateDirectory 负责 /var/lib/langshift-ops。不要复制 macOS .venv，不用生产机器练习。先审核/验证单元，再经批准安装到 /etc/systemd/system/ops-worker.service；以下只是在准备完成后可执行的验收命令，不是成功记录。

```bash
systemd-analyze verify systemd/ops-worker.service
sudo systemctl daemon-reload
sudo systemctl start ops-worker.service
sudo systemctl status ops-worker.service --no-pager
sudo journalctl -u ops-worker.service -n 30 --no-pager
sudo systemctl stop ops-worker.service
```

## 独立需求

只根据需求实现：两个目录 first/second，给 first 启动两次、second 一次，所有子进程 cwd 故意为 second，结果 [2,1]；独立状态不靠父进程内存共享。失败也必须只清理自己资源。参考 solutions/two_directories.py 与单独测试；先做再看答案。SIGTERM/SIGKILL 的差异、权限恢复、Linux待验证均应能口头解释。

## 环境矩阵（机器可读版本：ENVIRONMENT.json）

| 状态 | 证据与门槛 |
| --- | --- |
| 已实际运行 | 普通 macOS 用户；环境/cwd、缺失文件、SIGTERM/SIGINT清理与SIGKILL不清理、权限拒绝/恢复、loopback端口冲突、配置78/数据65/I-O74、两份独立状态目录。 |
| 本机不可运行 | 没有Linux/systemd；没有创建真实服务账户或安装系统单元。 |
| 用户需自备 | 可重建受控Linux/systemd主机、专用账户/组、经审核部署目录，以及安装单元的管理员授权。 |
| 待环境验收 | 目标机systemd配置验证、实际启停/失败重启/权限限制；启用开机启动前另做生命周期测试。Windows、并发写与断电持久性不在通过范围。 |

本轮标准 **16**、独立 **1** 个测试通过。源码与文稿 `implemented`；矩阵中的外部环境 `environment_pending`，不是整体部署通过。普通 macOS 测试不能代替 Linux/容器/公网或 Windows 证据。

## 恢复学习与排错记录

记录源码/锁摘要、cwd、工具版本、最后成功命令、失败阶段与分类、实际测试数、环境矩阵和下次第一步。不要记录完整环境、真实 token、数据库 URL 或私钥。恢复先 `uv sync --locked`，再跑标准与自己写的独立测试。只有参考答案通过，不代表你能独立实现。

## 一手资料

SOURCES.json 保存 2026-09-28 核验的官方地址、作用范围、HTTP获取结果与SHA-256摘要。章节正文解释每个机制，README 提供离线运行入口。这里没有自动创建生产资源、安装系统软件或接受服务条款。
