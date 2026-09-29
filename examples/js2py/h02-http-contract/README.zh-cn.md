# H02：与 H04–H06 对齐的 HTTP 契约

版本 `h02-task-contract-v2-h04-aligned`。核验日期 2026-09-28。**本实验仍只有契约样本、纯函数预览和静态服务，没有任务 CRUD。**

## 主线与可选加固分开

前置 H01 的进程、请求、端口与可信边界。当前核心为 `/tasks` 与 `id/title/minutes/done/note`：title 保留原字形/首尾空白但不能全空白，minutes 为必填严格非负整数，done 为严格布尔值默认 false，note 可空默认 null，id 由服务生成。PATCH 省略字段保留、显式 note=null 清除、0/false 应用；空 PATCH 合法无变化。

分页为 limit 默认20、最大100，offset默认0且非负，按id排序，输出 `items/limit/offset/total`，没有 next_offset 或状态筛选。404 是文本 detail；422 是 detail 数组，畸形 JSON 也为422。title/minutes/done 不接受 null，未知正文键拒绝，输出不泄漏 internal_tag。

完整离线约定见 `CONTRACT.zh-cn.md`（英文 `CONTRACT.md`、繁体 `CONTRACT.zh-tw.md`）。项目、成员、身份和数据库关系属于未来 D/S 演进，不是当前字段。HEAD、未知query拒绝、413/415、自定义错误、Location与生产脱敏均不作为H04已经兑现的承诺；实际差距见 `gaps/h04-observations.json`。

## 文件语义

24份 `public/exchanges` 样本彼此独立。`kind` 标注拟定；`precondition.seed_tasks` 记录初始条件；`request` 和 `response` 描述交互，不是在线API额外返回的包装。request.body 为对象时按 JSON 编码；malformed-json 的字符串表示原始待发送文本，不再包一层JSON引号。204的response.body=null是“没有正文”的样本标记，不代表传输四个字符null。

下载创建样本实际HTTP200不等于执行创建并得到201；读取删除样本不会删除任务。wire文件是省略Date/长度等细节的可读摘录，不是抓包或HTTP编码器。check_example只检查样本不变量，preview_page处理已解析的Python值，两者不是H04模型验证或HTTP解析器。

## 环境与复现

固定 CPython3.13.15、pytest8.4.2，requires-python `>=3.13,<3.14`，package=false；实测 uv0.12.13、macOS、curl8.7.1。H02不安装FastAPI；维护者另用隔离副本核对H04的FastAPI0.135.1/Uvicorn0.42.0/Pydantic2.12.5。没有修改共享H04源码或锁。

仓库用户从根目录进入实验；下载用户进入解压的h02-http-contract，从uv sync开始。

```bash
cd examples/js2py/h02-http-contract
pwd
uv sync --locked --default-index https://pypi.org/simple
uv run --locked python --version
uv run --locked python contract_examples.py
uv run --locked python inspect_transport.py
uv run --locked python -m pytest -q
uv run --locked python -m pytest -q solutions/test_review_cases.py
```

契约脚本最后输出：

```text
checked 24 proposed exchanges; no CRUD requests executed
```

标准47项（43项样本/计算、4项真实HTTP），独立5项。真实传输输出：

```text
real GET example: HTTP 200; proposed POST: 201
real GET tasks: HTTP 404
real POST tasks: HTTP 501; no CRUD implemented
real HEAD example: HTTP 200; body bytes=0
real GET with Origin: HTTP 200; allow-origin=False
service_alive=True
owned_service_stopped=True
```

这些HEAD结果来自标准库静态工具，不是H04任务路由；H04 HEAD /tasks实测405。不要把一个工具的能力自动迁移为另一个应用的保证。

## 两个终端的真实请求

A、B都在实验根。A前台启动：

```bash
uv run --locked python -m http.server 8767 --bind 127.0.0.1 --directory public
```

`-m` 运行标准库模块；8767是监听端口；`--bind` 限定loopback；`--directory public` 相对A启动目录。等待请求时不返回提示符是正常行为。

B运行：

```bash
curl --noproxy '*' --max-time 3 --include 'http://127.0.0.1:8767/exchanges/create-ok.json'
curl --noproxy '*' --max-time 3 --include 'http://127.0.0.1:8767/tasks'
curl --noproxy '*' --max-time 3 --include --header 'Content-Type: application/json' --data-binary @requests/create.json 'http://127.0.0.1:8767/tasks'
curl --noproxy '*' --max-time 3 --include --fail-with-body 'http://127.0.0.1:8767/tasks'
echo $?
```

状态依次200/404/501/404，最后curl退出22。curl是客户端；`--noproxy '*'` 绕过代理并用引号防shell展开；`--max-time 3` 限整轮等待；`--include`显示头与正文；`--header`添加头；`--data-binary @...`从B目录原样读取文件并默认POST；`--fail-with-body`保留HTTP错误正文并产生非零退出。默认curl收到HTTP错误仍可退出0，不能把退出码等同HTTP状态。

```bash
curl --noproxy '*' --max-time 3 --include --header 'Origin: https://untrusted.invalid' 'http://127.0.0.1:8767/exchanges/create-ok.json'
curl --noproxy '*' --max-time 3 --include --request OPTIONS --header 'Origin: http://127.0.0.1:5173' --header 'Access-Control-Request-Method: POST' --header 'Access-Control-Request-Headers: content-type' 'http://127.0.0.1:8767/tasks'
```

分别200且无Allow-Origin、501。`--request OPTIONS`指定方法；头中域名不是连接目标，没有访问它。curl不执行浏览器响应共享政策，因此不证明浏览器CORS成功。CORS也不是认证、授权或完整CSRF防护。

回A按Ctrl+C，只停止自己的前台实例。自动工具使用另一个分配的loopback端口，只清理自己的子进程，不会停手动A。端口冲突时辨认自有实例或换端口，禁止按端口杀陌生进程。只公开public，不放.env、工程根、用户目录、符号链接或真实数据。

## 意图失败与独立变式

```bash
uv run --locked python -m pytest -q errors/test_wrong_contract.py
```

预期1项断言失败、退出1：错误断言把204写成200。正确修复是断言204与无正文、让客户端跳过JSON，而非改坏样本。错误文件不在默认tests中。失败是测试断言，不是HTTP500。

先自写第二页(limit1/offset1)、末页外空页、PATCH省略note、显式null四个正常交互，再写minutes=null与limit101两个422；解释空PATCH不变而0/false是真实设置。solutions给出五项纯计算/一致性测试与六份完整交互，不能把它们叫在线CRUD测试。

## 恢复与已验证边界

暂停记录v2契约版本、修改样本、目录、自有服务终端/端口、最后命令、47+5项结果与下次第一步；停止服务。恢复先跑离线检查和inspect_transport，再手动请求，不推断有以前创建的任务。

当前快照实测：H02样本、分页、独立变式、意图失败、静态传输；维护者还在隔离H04副本核对24个核心交互与5项差距。HEAD405、未知query被忽略、媒体类型错误422而非415、超过64KiB的合法JSON仍201是差距观察，不是新增核心承诺。源摘要保存在gaps记录中。

未实现/未验收：H02 CRUD、完整schema、登录/权限、数据库、并发幂等、正文限额执行、生产脱敏、真实浏览器CORS、TLS、公网、Linux/Windows执行、最终ZIP与全站集成。发布文件由外部同名-files.json显式列出，不含环境、缓存、日志或凭证。

## 一手资料

2026-09-28核对：[RFC9110](https://www.rfc-editor.org/rfc/rfc9110.html)、[RFC5789](https://www.rfc-editor.org/rfc/rfc5789.html)、[Pydantic严格模式](https://github.com/pydantic/pydantic/blob/v2.12.5/docs/concepts/strict_mode.md)、[响应模型](https://fastapi.tiangolo.com/tutorial/response-model/)、[部分更新](https://fastapi.tiangolo.com/tutorial/body-updates/)、[错误处理](https://fastapi.tiangolo.com/tutorial/handling-errors/)、[Fetch/CORS](https://fetch.spec.whatwg.org/#http-cors-protocol)、[http.server](https://docs.python.org/3.13/library/http.server.html)、[http.client](https://docs.python.org/3.13/library/http.client.html)、[curl](https://curl.se/docs/manpage.html)。
