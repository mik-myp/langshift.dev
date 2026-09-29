# O03 HTTPS、入口代理与生产边界

前置 O02。诊断工具只在127.0.0.1上运行；没有真实认证/任务数据库，不能公开。S阶段实际方案是不透明Authorization Bearer会话，DB摘要+expiry/revoked+auth_version，不用JWT或认证Cookie；本工具仅证明虚构头被传递，绝不证明认证成功。

## 环境与恢复

核验日期：**2026-09-28**。需要普通 POSIX 账户；不以 root 运行权限实验。CPython **3.13.15**、uv **0.12.13**、pytest **8.4.2**。`.python-version` 选解释器，pyproject 声明 `>=3.13,<3.14`，uv.lock 锁依赖；`[tool.uv] package=false` 表示不打包这个练习为可发布 Python 包。

Web 基线：FastAPI **0.135.1**、Uvicorn **0.42.0**、Pydantic **2.12.5**、HTTPX **0.28.1**、Starlette **0.52.1**、AnyIO **4.12.1**；没有前端依赖。

仓库用户从仓库根目录执行下列 cd；ZIP 用户直接进入解压后的同名实验根目录，里面应有 pyproject.toml。`--locked` 拒绝悄悄更新锁。

```bash
cd examples/js2py/o03-https-production
pwd
uv --version
uv sync --locked
uv run --locked python --version
```

维护者锁文件已用 `uv lock --default-index https://pypi.org/simple` 实际生成。读者恢复不需要重新解析。环境与缓存不进清单/ZIP，所有数据实验用自己创建的临时目录。

额外系统工具：OpenSSL3.x支持 req -addext/-noenc（本轮3.6.4）、curl（本轮8.7.1）。不自动安装系统软件。certificates.py仅在自有/tmp目录生成一天有效的临时CA与lab.test叶证书，目录0700/文件0600，不安装系统信任、不打包、不打印私钥。

```bash
openssl version
curl --version
uv run --locked python tls_lab.py
uv run --locked python -m pytest -q
uv run --locked python -m pytest -q solutions/test_origin_policy.py
uv run --locked python check_config.py
```

```text
trusted_ca_https=200
unknown_ca_curl_exit=60
wrong_hostname_curl_exit=60
edge_overwrites_forged_forwarding=True
authorization_forwarded_not_authenticated=True
untrusted_proxy_headers_ignored=True
trusted_loopback_direct_spoof_possible=True
sanitized_error=500
sanitized_validation=422
teaching_edge_body_limit=413
owned_processes_stopped_and_temp_keys_removed=True
```

## 双终端交互与停止

终端A运行下列命令。--serve保持前台；--port 0让OS选空闲端口。把程序实际打印的export CA和export PORT行复制到终端B；CA是公开信任材料路径，不是私钥。终端B仍在实验根目录运行curl。--resolve仅覆盖这一次客户端的DNS映射，保留SNI/Host；--cacert启用指定CA校验，--noproxy避开外部代理，--max-time限制等待，--include显示响应头，-H添加请求头。

```bash
uv run --locked python tls_lab.py --serve --port 0
```

```bash
curl --silent --show-error --include --max-time 5 --noproxy '*' --resolve "lab.test:$PORT:127.0.0.1" --cacert "$CA" -H 'Authorization: Bearer demo-not-a-valid-session' "https://lab.test:$PORT/probe"
```

预期200、scheme=https、authorization_present=true，但并未认证。去掉--cacert或改URL与resolve名字为wrong.test，各自curl exit60；严禁用-k算验收。终端A的Ctrl+C停止自有后端/边缘并删除临时密钥；旧CA路径随后失效，下次启动重新复制。自动模式同样清理，绝不killall。

## 机制与故意缺口

edge.py是有界标准库教学转发器，不是生产HTTP解析器。只接受限定请求头，覆盖Forwarded类信息；4096字节body限制返回413仅对本边缘成立，不替H04/S03承诺策略。app.py返回安全500与loc/type-only422，不回显输入/traceback，日志只安全事件和随机id；/fail只供本地故障实验。

关闭代理信任会忽略伪造头；通过边缘会被覆盖；但受信127.0.0.1上游可被同机其他进程直连伪造。该观察是真实残余风险，必须通过实际部署隔离解决，不能用allow-ips=*修URL。TLS不负责查会话、成员授权或撤销。

精确来源CORS只允许演示GET/POST及Authorization/Content-Type/Idempotency-Key；真实S API另需完整方法策略。allow_credentials=False、不用Cookie；CORS不是认证，curl不执行浏览器读取限制。若改Cookie须重新评估CSRF/SameSite/Secure/HttpOnly/来源和反CSRF机制。真实浏览器未验收。

## Caddy/公网（未实跑）

Caddyfile.local使用同主机loopback上游8034和显式TLS_CERT/TLS_KEY路径；production.template保留api.example.invalid，不可直接发布。caddy缺失，所以只执行check_config文本不变量检查，没有caddy validate/运行证据。若在自己的受控主机准备固定Caddy、独立证书与目标应用，可先单独启动下面的本地诊断上游供配置测试；这不是生产服务。需要自行准备证书路径再验证本地配置，不得借用用户真实私钥。

```bash
uv run --locked python -m uvicorn app:create_app --factory --host 127.0.0.1 --port 8034 --proxy-headers --forwarded-allow-ips 127.0.0.1 --no-access-log
caddy validate --config Caddyfile.local --adapter caddyfile
```

上面第一条是前台命令，第二条在另一终端且已准备证书环境时运行；结束第一条用Ctrl+C。不同容器不能用彼此的loopback通信；拓扑改变须重审上游/信任边界。公网DNS、公签证书签发续期、访问限制、完整S03认证撤销与DB ready、请求大小和登录节流、发布回退与备份恢复都仍待验收；不创建任何公开资源。

## 独立需求

允许frontend.lab.test:8444与admin.lab.test:8445两个精确HTTPS来源；错端口、HTTP、恶意域名后缀与null预检拒绝。不用Cookie，不把无Origin直接调用称为认证。先写实现与测试，再看solutions/origin_policy.py的7个独立case。

## 环境矩阵（机器可读版本：ENVIRONMENT.json）

| 状态 | 证据与门槛 |
| --- | --- |
| 已实际运行 | 临时CA/叶证书与权限、curl --cacert成功及未知CA/错主机名exit60、loopback TLS、转发头覆盖/忽略与同机直连伪造缺口、虚构Authorization传递、脱敏500/422、教学413、CORS头、清理。 |
| 本机不可运行 | 无Caddy、无受控Linux/容器环境；未提供用户域名、主机或生产秘密。 |
| 用户需自备 | 受控主机与固定反代版本、自有域名/DNS、防火墙/挑战端口许可、生产秘密与证书持久存储、实际浏览器前端及完整S03服务。 |
| 待环境验收 | caddy validate与运行、真实A/AAAA/公网连通、公签证书申请续期、上游不可绕过/多代理信任、真实浏览器、Cookie变更时CSRF重评估、S03撤销/授权/DB ready、生产body限制/登录节流/哈希容量、迁移回退与备份恢复。 |

本轮标准 **17**、独立 **7** 个测试通过。源码与文稿 `implemented`；矩阵中的外部环境 `environment_pending`，不是整体部署通过。普通 macOS 测试不能代替 Linux/容器/公网或 Windows 证据。

## 恢复学习与排错记录

记录源码/锁摘要、cwd、工具版本、最后成功命令、失败阶段与分类、实际测试数、环境矩阵和下次第一步。不要记录完整环境、真实 token、数据库 URL 或私钥。恢复先 `uv sync --locked`，再跑标准与自己写的独立测试。只有参考答案通过，不代表你能独立实现。

## 一手资料

SOURCES.json 保存 2026-09-28 核验的官方地址、作用范围、HTTP获取结果与SHA-256摘要。章节正文解释每个机制，README 提供离线运行入口。这里没有自动创建生产资源、安装系统软件或接受服务条款。
