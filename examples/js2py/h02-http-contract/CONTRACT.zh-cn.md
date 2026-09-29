# 任务接口契约 h02-task-contract-v2-h04-aligned

2026-09-28。当前阶段与H04对齐，仍是提案而非H02在线CRUD。只用虚构数据。运行和包装语义见README.zh-cn.md。后面的可选加固差距不是当前核心承诺，项目/身份/数据库字段留给D/S显式演进。

## 3. 资源与方法：HTTP 语义不等于框架自动实现

`/tasks` 表示任务集合，`/tasks/1` 表示其中一项。资源不是本机文件，也不是数据库表的直接地址。H02 的静态服务器恰好把路径映射到文件，后续路由则把路径交给业务处理；相同的 HTTP 外形可以连接不同实现。

| 方法 | 语义与当前范围 |
| --- | --- |
| GET | 读取集合或单项，不借读取动作创建或删除任务 |
| POST | 向集合提交创建要求；由服务分配 id；重复提交可能创建两项 |
| PATCH | 修改明确提供的字段；本契约使用绝对值设置，不是完整替换 |
| DELETE | 移除指定任务；重复后的状态可变，目标仍是让它不存在 |
| HEAD | HTTP 中与 GET 对应但不返回正文；**不在 H04 的已实现方法清单中** |
| PUT | 通常表达目标资源状态的替换；本版不支持，不能当作 PATCH 的别名 |

GET 的“安全”表示调用者不要求业务状态改变，不表示不写访问日志或没有安全风险。安全方法、PUT 和 DELETE 具有 HTTP 规定的幂等语义，POST 没有通用幂等保证。PATCH 是否可安全重复，需要看具体补丁含义。[RFC 9110 §9](https://www.rfc-editor.org/rfc/rfc9110.html#section-9)、[RFC 5789](https://www.rfc-editor.org/rfc/rfc5789.html)

标准定义 HEAD 的语义，不代表每个框架的 GET 声明都会自动注册 HEAD。H01 静态工具对 HEAD 返回 200，而当前 H04 对 `/tasks` 的 HEAD 实测 405；这不是让你忽略协议，而是提醒你分别核对“协议如何定义”和“应用实际支持什么”。


## 4. 核心字段：原样、严格类型、默认值与输出边界

本版名为 `h02-task-contract-v2-h04-aligned`。离线完整约定在 `CONTRACT.md`、`CONTRACT.zh-cn.md`、`CONTRACT.zh-tw.md`。下面是与当前 H04 模型一致的输入与输出，不把未来多用户字段提前放入当前 API。

| 字段 | POST 创建 | PATCH 修改 | 成功响应与约束 |
| --- | --- | --- | --- |
| `title` | 必填字符串 | 可省略；提供时不能为 null | 原字符串长度 1–120；全部空白拒绝；验证时检查去空白副本，**保存和返回原字形及首尾空白** |
| `minutes` | 必填普通整数 | 可省略；提供时不能为 null | 大于等于 0；拒绝 true、字符串数字和浮点数，不自动强制转换 |
| `done` | 可省略，默认 false | 可省略；提供时不能为 null | 严格布尔值，只接受 JSON true/false，不接受 0/1 或字符串 |
| `note` | 可省略，默认 null | 省略保留；null 清除；字符串替换 | null 或最长 1000 字符的字符串；空字符串也是合法值 |
| `id` | 禁止客户端提供 | 禁止客户端提供 | 服务分配的正整数；不承诺跨重启唯一或全局唯一 |

字符串长度按 Python 字符串的码点计数，不按 UTF-8 字节或可见字形。`"  Ship the draft  "` 合法且空白保留；`"   "` 不合法。把“不能全空白”偷换成“保存时 trim”会改变用户数据，前后端不能各自猜一种规则。

POST/PATCH 正文是 JSON 对象，未知字段拒绝为 422，包括自报 id 或内部字段。成功任务只有 `id/title/minutes/done/note`；H04 故意在存储中加入 `internal_tag`，但它不应出现在 HTTP 输出。输出模型是公开字段白名单，不是把整个存储对象直接透传。

正文的严格类型与 URL 参数的解析不是一回事：JSON 自带数字、布尔值等类型，查询和路径则先以文本到达。不要从“minutes 严格整数”推出“所有 query 参数必须按相同字面形式校验”。[Pydantic strict mode](https://github.com/pydantic/pydantic/blob/v2.12.5/docs/concepts/strict_mode.md)、[FastAPI 响应模型](https://fastapi.tiangolo.com/tutorial/response-model/)


## 5. PATCH 的关键不是“可选”，而是有没有提供这个键

假设已有任务 note 为 `keep me`。只提交 `{"done": true}`，表示只修改完成状态，note 必须保留；提交 `{"note": null}` 才明确清除。`{"note": ""}` 又是第三种有意义的输入：保存空字符串。它们不能全部被一次“过滤空值”合并成相同操作。

同理，minutes 为 0 和 done 为 false 都是有效的显式修改，不能用 JS 的 `if (value)` 或 Python 的真假判断来决定是否应用。判断的是**键是否出现**。H04 将以 `exclude_unset=True` 提取已提供字段；这里先建立语义，不先要求背模型 API。

**空 PATCH 对象 `{}` 是合法的无变化更新，返回 200 与原任务。** 默认值服务于模型构造，不意味着省略字段就要重置存储。minutes/title 的内部占位默认值不能覆盖已有值，note 的默认 null 也不能清除省略字段。只有 note 接受显式 null；title/minutes/done 的 null 为 422。

所有修改先验证，再整体替换学习版内存记录；一次失败 PATCH 不应留下标题已改、minutes 未改的半成品。这是单次处理的约定，不是对多进程、并发读改写或数据库事务的保证。H04 的单进程字典只是学习实现，重启会丢数据，后面才建立持久化与并发边界。[FastAPI 部分更新](https://fastapi.tiangolo.com/tutorial/body-updates/)


## 6. 从请求到响应：当前明确支持的交互

| 请求 | 正常结果 | 失败与边界 |
| --- | --- | --- |
| `GET /health` | 200，`{"status":"ok"}` | 仅表明该处理路径能响应，不证明任务正确、数据库可用或有权限 |
| `POST /tasks` | 201，完整公开任务 | 缺字段、非法类型、空白标题、额外字段为 422；没有标题唯一约束 |
| `GET /tasks` | 200，`items/limit/offset/total` | 分页参数不合要求为 422；空集合仍是成功 |
| `GET /tasks/{task_id}` | 200，完整公开任务 | id 要大于 0；非法 id 为 422，合法但不存在为 404 |
| `PATCH /tasks/{task_id}` | 200，完整修改后任务 | 按第 5 节保留/替换；不存在为 404，非法输入为 422 |
| `DELETE /tasks/{task_id}` | 204，没有正文 | 再次删除为 404；客户端不解析成功响应的 JSON |

提供给读者的规范路径没有结尾斜杠。**不在 H02 额外承诺尾斜杠一定 404 或一定无重定向**；框架行为必须另测。也不为 ID 增加 H04 未实施的 JavaScript 安全整数上限或“禁止前导零”等新规则。

无此资源得到 404，不能与“服务没启动”的连接失败混淆；不支持的方法通常得到 405，响应带 Allow 表示路由器报告的允许方法。当前路由声明的组合不保证 Allow 是整张表的完整并集，不能根据自己写的表伪造一条头部快照。样本保留实际核对结果，客户端不要把这个头当授权许可。

此时没有登录、项目成员或任务所有权。id 不是权限证明，能猜到编号不应在未来自动取得访问权，但**当前学习版根本没有实施那层检查**。所以既不把样本称为安全 API，也不要求当前客户端发送尚未定义的身份字段。


## 7. 错误：沿用 detail，仍要解释清楚每种失败

本版沿用 FastAPI 的错误形态：不存在任务是 `{"detail":"Task not found"}`；请求验证失败是 `{"detail":[...]}`。不把自创的 `error/code/message/fields` 信封描述为后续默认会实现的行为。

```json
{
  "kind": "proposed-contract-example",
  "name": "blank-title",
  "precondition": {
    "seed_tasks": []
  },
  "request": {
    "method": "POST",
    "target": "/tasks",
    "headers": {
      "Content-Type": "application/json"
    },
    "body": {
      "title": "   ",
      "minutes": 15
    }
  },
  "response": {
    "status": 422,
    "headers": {
      "Content-Type": "application/json"
    },
    "body": {
      "detail": [
        {
          "type": "value_error",
          "loc": [
            "body",
            "title"
          ],
          "msg": "Value error, title must not be blank",
          "input": "   ",
          "ctx": {
            "error": {}
          }
        }
      ]
    }
  }
}
```

外层 `kind/precondition/request/response` 是**教学样本包装**；在线 API 只发送其中 response.body。precondition 记录这个独立案例假定的初始任务，不是新增网络字段。验证项里 `loc` 定位 body/query/path 和字段，`type` 描述错误种类，`msg` 是解释文本；有时还包含 input/ctx。客户端可据位置标出字段错误，不应依赖英文句子的某个词、数组顺序或所有辅助键始终存在。

| 观察 | 应如何理解 |
| --- | --- |
| 201 + 公开任务 | 创建成功，保存返回的 id；不假定有 Location |
| 204 + 零字节正文 | 删除成功，跳过 JSON 解析 |
| 404 + 文本 detail | 合法编号对应的任务不存在；不是网络断线 |
| 422 + detail 数组 | 参数或正文验证失败；根据 loc/type 修正请求 |
| 畸形 JSON 也为 422 | 当前 FastAPI 使用 json_invalid；不要把自己偏好的 400 写成当前事实 |
| 405 + 文本 detail | 此路径没有对应方法处理器；不等于未认证 |
| 未预期的 500 | 服务端故障，不应自动当成安全重试信号；也不承诺它使用验证错误的 JSON 格式 |

HTTP 中 400、401、403、409、413、415 都有各自用途：请求错误、身份、权限、业务冲突、过大正文和不支持的媒体类型。但**知道状态码的含义，不等于本阶段已实现对应政策**。例如当前无身份验证，也无冲突唯一性规则，不能凭空要求重复标题变成 409。[RFC 9110 §15](https://www.rfc-editor.org/rfc/rfc9110.html#section-15)

默认验证错误可能回显输入。它适合观察虚构实验数据，但不是生产脱敏保证；不要提交真实凭证，再把错误贴进日志或工单。后续若统一错误信封或脱敏，需要明确版本变化和兼容策略，而不是只在教材里改示例。[FastAPI 错误处理](https://fastapi.tiangolo.com/tutorial/handling-errors/)


## 8. 分页：把排序、总数和下一次请求拆开

`GET /tasks` 的 limit 默认 20、范围 1–100；offset 默认 0、必须大于等于 0。服务按 id 升序排列全部当前任务，再切片；total 是切片前总数，不是当前页长度。查询参数由框架解析，本章不新增一套严格字符串语法，也不承诺未知或重复 query 自动拒绝。

```json
{
  "kind": "proposed-contract-example",
  "name": "list-first",
  "precondition": {
    "seed_tasks": [
      {
        "title": "  Read HTTP  ",
        "minutes": 25,
        "done": false,
        "note": "keep me"
      },
      {
        "title": "Check the failure path",
        "minutes": 0,
        "done": true,
        "note": null
      },
      {
        "title": "Write an independent case",
        "minutes": 40,
        "done": false,
        "note": "later"
      }
    ]
  },
  "request": {
    "method": "GET",
    "target": "/tasks?offset=0&limit=2",
    "headers": {}
  },
  "response": {
    "status": 200,
    "headers": {
      "Content-Type": "application/json"
    },
    "body": {
      "items": [
        {
          "id": 1,
          "title": "  Read HTTP  ",
          "minutes": 25,
          "done": false,
          "note": "keep me"
        },
        {
          "id": 2,
          "title": "Check the failure path",
          "minutes": 0,
          "done": true,
          "note": null
        }
      ],
      "limit": 2,
      "offset": 0,
      "total": 3
    }
  }
}
```

```json
{
  "kind": "proposed-contract-example",
  "name": "list-last",
  "precondition": {
    "seed_tasks": [
      {
        "title": "  Read HTTP  ",
        "minutes": 25,
        "done": false,
        "note": "keep me"
      },
      {
        "title": "Check the failure path",
        "minutes": 0,
        "done": true,
        "note": null
      },
      {
        "title": "Write an independent case",
        "minutes": 40,
        "done": false,
        "note": "later"
      }
    ]
  },
  "request": {
    "method": "GET",
    "target": "/tasks?offset=2&limit=2",
    "headers": {}
  },
  "response": {
    "status": 200,
    "headers": {
      "Content-Type": "application/json"
    },
    "body": {
      "items": [
        {
          "id": 3,
          "title": "Write an independent case",
          "minutes": 40,
          "done": false,
          "note": "later"
        }
      ],
      "limit": 2,
      "offset": 2,
      "total": 3
    }
  }
}
```

第一页 offset=0、limit=2，得到 id 1、2，total=3；第二页 offset=2，得到 id 3。响应**没有 next_offset**。客户端根据 `offset + items.length < total` 判断这次观察是否还有后续数据，下一次可请求 offset+limit。offset=99 则得到 200、空 items、total=3，不是 404：集合存在与单项存在是两件事。

当前没有 done/status 筛选接口。给 URL 加 `done=true` 不会自动产生过滤功能；在当前 H04 中这类未知 query 被忽略。需要筛选时应先修订契约，再加解析、过滤、计数与测试，不能让前端以为已经筛过。

稳定排序只解决同一数据集的顺序，不提供跨请求快照。第一页后有人删除较前面的任务，下一页的 offset 可能跳过一项；并发变化也可能令 total 过时。当前接受这个限制，不承诺每页组合就是某个时刻的完整快照，更不偷渡数据库隔离或游标实现。

```python
"""H04-aligned proposed samples, NOT a CRUD backend or request validator."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASE_NAMES = (
    "list-first", "list-last", "list-empty", "list-default", "get-task",
    "create-ok", "patch-title", "patch-clear-note", "delete-ok", "delete-again",
    "missing-task", "blank-title", "bad-page", "bool-minutes", "wrong-method",
    "malformed-json", "null-title", "server-field", "missing-minutes",
    "string-minutes", "nonbool-done", "empty-patch", "patch-zero-false",
    "patch-omit-note",
)
PUBLIC_FIELDS = {"id", "title", "minutes", "done", "note"}


def read_case(name: str) -> dict:
    if name not in CASE_NAMES:
        raise ValueError("unknown contract example")
    return json.loads((ROOT / "public" / "exchanges" / f"{name}.json").read_text(encoding="utf-8"))


def check_task_example(task: dict) -> None:
    """Selected output invariants, not a substitute for H04's Pydantic models."""
    if set(task) != PUBLIC_FIELDS:
        raise ValueError("public task fields must match the core contract")
    if type(task["id"]) is not int or task["id"] <= 0:
        raise ValueError("id must be a positive integer")
    if not isinstance(task["title"], str) or not 1 <= len(task["title"]) <= 120 or not task["title"].strip():
        raise ValueError("title must be a nonblank string of 1..120 characters")
    if type(task["minutes"]) is not int or task["minutes"] < 0:
        raise ValueError("minutes must be a nonnegative integer, not bool")
    if type(task["done"]) is not bool:
        raise ValueError("done must be bool")
    if task["note"] is not None and (not isinstance(task["note"], str) or len(task["note"]) > 1000):
        raise ValueError("note must be null or a string of at most 1000 characters")


def check_example(example: dict) -> None:
    """Check selected sample consistency, not arbitrary HTTP input or state."""
    if example["kind"] != "proposed-contract-example":
        raise ValueError("example must be marked as proposed")
    response = example["response"]
    status, headers, body = response["status"], response["headers"], response["body"]
    if status == 204:
        if body is not None or "Content-Type" in headers:
            raise ValueError("204 must not promise a JSON body")
        return
    if headers.get("Content-Type") != "application/json":
        raise ValueError("these core examples use JSON except for 204")
    if status >= 400:
        if set(body) != {"detail"}:
            raise ValueError("core errors use detail, not a custom error envelope")
        if status == 422:
            if not isinstance(body["detail"], list) or not body["detail"]:
                raise ValueError("422 needs a nonempty validation detail list")
            for issue in body["detail"]:
                if not {"loc", "type", "msg"} <= set(issue):
                    raise ValueError("validation details need loc/type/msg")
        elif not isinstance(body["detail"], str):
            raise ValueError("404/405 examples use a text detail")
        return
    if isinstance(body, dict) and "items" in body:
        if set(body) != {"items", "limit", "offset", "total"}:
            raise ValueError("page must not invent next_offset or filtering metadata")
        if not 1 <= body["limit"] <= 100 or body["offset"] < 0 or body["total"] < len(body["items"]):
            raise ValueError("invalid page metadata")
        if len(body["items"]) > body["limit"]:
            raise ValueError("page exceeds limit")
        for task in body["items"]:
            check_task_example(task)
    else:
        check_task_example(body)
    if status == 201 and body["title"] != example["request"]["body"]["title"]:
        raise ValueError("creation preserves original title spelling and spaces")


def preview_page(tasks: list[dict], offset=0, limit=20) -> dict:
    """Pure preview of parsed values. Not a query parser, filter, or database."""
    if type(offset) is not int or offset < 0:
        raise ValueError("offset must be a nonnegative integer")
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    ordered = sorted(tasks, key=lambda task: task["id"])
    return {"items": ordered[offset:offset + limit], "limit": limit,
            "offset": offset, "total": len(ordered)}


if __name__ == "__main__":
    for name in CASE_NAMES:
        example = read_case(name)
        check_example(example)
        request = example["request"]
        print(f"PROPOSED {request['method']} {request['target']} -> {example['response']['status']}")
    print(f"checked {len(CASE_NAMES)} proposed exchanges; no CRUD requests executed")
```

preview_page 只计算**已解析 Python 值**的排序与分页，check_example 只验证列出的样本不变量。二者不是 HTTP 解析器、完整 Pydantic 替身或 CRUD 状态机；通过这些检查不代表后端已经实现。


## 9. 幂等：比较预期效果，而非每次状态相同

第一次 DELETE 成功而响应丢失，再次 DELETE 得到 404，并不破坏“该任务不存在”的效果。幂等关注同样请求重复后的预期业务效果，不要求响应字节或状态完全一样，也不禁止多一条访问日志。当前 id 可能在进程重启后重用，因此不能无限期重试旧编号，再声称仍在操作同一资源。

POST 则可能第一次已创建、只是响应没到达；重复发送同一标题会创建第二项。超时说明客户端没有及时拿到结果，不证明服务端没做事。禁用提交按钮只减少这份 UI 中的误点，不能覆盖网络重试、多设备或重新打开页面。

当前 PATCH 设置绝对值，例如 `{"done": true}`，不是“切换状态”。在同一目标仍存在、无其他写入、无额外副作用的条件下，重复相同设置得到相同字段状态；这不意味着所有 PATCH 都幂等。以后加入累加、通知或并发版本检查，必须重新分析业务效果。[RFC 5789 §2](https://www.rfc-editor.org/rfc/rfc5789.html#section-2)

本章没有 Idempotency-Key 存储、事务或去重响应缓存。多传一个头部不会自动获得恰好一次语义。现在不自动重试 POST；写操作超时时先保留“结果未知、待确认”，不要把它错误显示成确定的创建失败。可靠重试留到 S03，必须说明键归属、有效期、同键不同请求与并发处理。


## 10. 可选加固与当前差距：不能把愿望写成已实现契约

以下是 2026-09-28 对当前 H04 隔离副本的实际观察，不是新增主线要求。完整记录在 `gaps/h04-observations.json`，带源码摘要，便于以后判断实现是否变化。

| 可选政策 | 当前观察／边界 | 若以后采用，必须补什么 |
| --- | --- | --- |
| 自动支持 HEAD | HEAD /tasks 为 405；H01 静态工具却支持 | 显式方法支持、无正文与错误路径测试 |
| 拒绝未知 query | `done=true` 被忽略，仍返回未过滤列表 | 参数模型、拒绝规则、调用方迁移 |
| 统一媒体类型错误为 415 | text/plain 和缺 Content-Type 的实验均为 422 | 入口检查、允许媒体类型/charset 和一致错误策略 |
| 限制整段正文到 64 KiB 并返回 413 | 70000 个空格加合法短 JSON 的 POST 为 201 | 明确按字节限额，在完整读取前限制，并验证代理/应用两层 |
| 统一自定义错误、禁止输入回显 | 默认 detail 可能携带 input | 异常映射、脱敏、客户端兼容与负向测试 |

字段 note 长度上限不等于整个请求体的字节限制；有健康响应也不等于具备这些政策。当前观察只适用于记录的基线，不能把“没配置限额”解读成平台保证无限接收。可选加固都应有独立需求与验收，不偷偷让初学者在 H04 必测用例中追一个不存在的承诺。

