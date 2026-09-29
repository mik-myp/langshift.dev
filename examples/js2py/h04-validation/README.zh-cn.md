# H04 — Pydantic 输入输出边界与内存 CRUD

[English](README.md) · [繁體中文](README.zh-tw.md)

这是完整、独立的本地 API，不是生产存储。前置为 H03 同步服务与 L11/L12 注解和模型，不导入其他章节实现。API 自动测试与 fixture 在 H06 正式教学；本实验读者使用完全可见的 curl 做验收。

## 复现环境

**2026-09-28** 在 macOS arm64 实测：CPython **3.13.15**、uv **0.12.13**、FastAPI **0.135.1**、Uvicorn **0.42.0**、Pydantic **2.12.5**。这是验收版本，不是“最新”承诺。公开 PyPI 的 `uv.lock` 固定间接依赖，包括 Starlette 1.7.0、pydantic-core 2.41.5。`requires-python` 为 `>=3.13,<3.14`；`[tool.uv] package=false`。不需要前端依赖、数据库、API key、httpx 或 pytest。

工作目录为解压的 `h04-validation`，或仓库的 `examples/js2py/h04-validation`。以下应用、探针与答案命令均从此目录运行。

```bash
uv --version
uv python install 3.13.15
uv sync --locked
uv run --locked python --version
```

维护者在 uv 命令前设置隔离位置：

```bash
export PATH="$HOME/.local/bin:$PATH"
export UV_PYTHON_INSTALL_DIR=/tmp/langshift-js2py-python-20260928
export UV_CACHE_DIR=/tmp/langshift-js2py-uv-cache-20260928
```

普通读者可用 uv 默认位置；临时目录不是项目输入。正常运行不重新生成锁文件。维护者解析使用 `uv lock --default-index https://pypi.org/simple`，安装与执行使用 `--locked`。

## 正文与路由契约

| 字段 | 创建 | PATCH |
| --- | --- | --- |
| title | 必填 str，1–120 字符，不能全为空白，保留原字形与两侧空白 | 遗漏保留，合法字符串替换，null 拒绝 |
| minutes | 必填严格非负 int，拒 bool、text、float | 遗漏保留，0 也应用，null 拒绝 |
| done | 严格 bool，默认 False | 遗漏保留，显式 false 也应用，null 拒绝 |
| note | str 或 None，最多 1000 字符，默认 None，空串合法 | 遗漏保留，字符串替换，null 清空 |
| id | 服务生成进程内递增正整数 | 客户端字段拒绝 |
| internal_tag | 服务添加 `h04-memory-only` | 客户端字段拒绝，永不公开 |

长度按 Python 字符串计算，不是字节数或视觉字形。未知字段包括 `id`、`user_id`、`internal_tag` 均为 422。拒绝自报身份不等于认证身份：这里没有用户概念。

- `GET /health`：200，`{"status":"ok"}`。
- `POST /tasks`：201，完整公开任务；缺字段、畸形 JSON 或不合法正文为 422。
- `GET /tasks`：200，`{items, limit, offset, total}`，按 id 排序。`limit=20` 默认，范围 1–100；`offset=0` 默认，非负；非法查询为 422。超出末尾是空页，不是 404。
- `GET /tasks/{task_id}`：200，公开任务；合法但不存在 id 为 404；非法 id 为 422。
- `PATCH /tasks/{task_id}`：200，完整更新后公开任务；`{}` 不修改。非法字段 422；合法正文但记录不存在为 404。
- `DELETE /tasks/{task_id}`：204，**正文零字节**；不存在/重复删除为 404。

没有 PUT、认证、用户隔离、项目关系、幂等键或最终 capstone 状态枚举。创建/读取/更新和列表 items 中公开任务恰好包含 `id`、`title`、`minutes`、`done`、`note`。

## 请求前先理解模型流向

`models.py` 区分 `TaskCreate`、`TaskPatch`、`TaskStored`、`TaskPublic`。输入严格验证并拒绝未知键；title 检查 `value.strip()` 但返回原 `value`。公开模型故意忽略白名单外字段，`TaskPage` 对列表内记录执行同样规则。

运行两个讲解探针：

```bash
uv run --locked python probe_models.py
uv run --locked python probe_patch.py
```

第一个对比宽松转换 `"25"` 和严格拒绝 `True`、`"25"`、`25.0`，并拒绝负整数；证明没有默认值的 `str | None` 仍必填。它们只是模型实验，不是 HTTP 验收。

`TaskPatch` 有合法占位默认值：`title="Untitled"`、`minutes=0`、继承的 `done=False`、`note=None`，从而支持省略非 nullable 字段。**只有 `model_dump(exclude_unset=True)` 可以合并到存储。** 占位值不是更新指令。显式 false、0、等于默认值的 title、null 都必须保留。`exclude_none` 丢清空意图，`exclude_defaults` 丢 false/0；探针同时打印正确合并与故意错误的 dump。

`app.py` 在临时字典中合并，调用 `TaskStored.model_validate` 后才替换记录。`model_copy(update=...)` 不会自动验证更新。id/内部字段不来自请求；处理函数故意返回完整存储字典，由 `response_model` 过滤实际 HTTP 输出，避免把“没有存内部键”误当“确实完成过滤”。

## 启动空服务，运行工作单

终端 A：

```bash
uv run --locked python -m uvicorn app:app --host 127.0.0.1 --port 8004 --workers 1
```

不启用 reload，不暴露 `0.0.0.0`。`--workers 1` 显式覆盖外部默认设置，但不消除线程池并发。终端 B：

```bash
curl -sS -i http://127.0.0.1:8004/tasks
bash requests.sh
```

`requests.sh` 从空内存开始，发送 **25** 次可见请求。它打印而不自动断言；必须阅读响应，curl 默认退出码即便收到 HTTP 错误也可能为零。`-i` 显示状态/头，`-X` 选方法，`-H 'Content-Type: application/json'` 标明 JSON，`--data-binary` 发原正文。JSON 和含 `&` 的 URL 应加引号。

核对顺序：

1. 空列表、两个 201、第二页 id=2/total=2，title 空白保留。
2. PATCH done 保留 note；`{}` 不变；false/0 应用；note 能替换与显式 null 清空。
3. 八个错误正文全为 422，没有新记录。
4. 非法路径/查询 422；合法但不存在 id 为 404。
5. GET 与存储一致；DELETE 正文零字节；读取/重复删除为 404；最后只留 id=2。任务响应都不包含 `internal_tag`。

第一次创建的实际正文：

```json
{"id":1,"title":"  Read HTTP  ","minutes":25,"done":false,"note":"keep me"}
```

`minutes=true` 为 422，`loc=["body","minutes"]`、`type="int_type"`；与合法但不存在 id 的 404 不同。错误可能回显输入，因此只用虚构数据，不能把默认错误格式当成生产脱敏政策。

自行补测缺 title/minutes、`done=1`、`note=1`、非 nullable 字段 null、自报 id/内部字段、畸形 JSON、长度边界：120/1000 通过，121/1001 拒绝。可在本地文件准备长正文，用 `--data-binary @payload.json` 发送。被拒 PATCH 后 GET 不应发生部分修改。记录状态和字段，而不是只写“请求成功”。

## 破坏性重启与恢复：仅可丢弃数据

工作单执行后 id=2 仍在，在终端 A Ctrl-C 退出**自己的**服务，再用同一命令重启。GET `/tasks` 应 items 为空、total=0；GET `/tasks/2` 应为 404；新建 id 又为 1。这是实际数据丢失与 id 重用，没有备份或数据库能恢复旧内存。

恢复学习检查点的方法是重启为空，再重放工作单。不关闭别人的监听者。端口冲突时停止自己的服务或换空闲端口并同步改 URL；导入错误时先核对工作目录与 `app:app` 两侧，不要先重装依赖。

## 独立重建与变式

在新目录只保留环境文件与契约，自写模型/CRUD，解释四类模型，通过请求验收后再看答案。记录一个问题的现象、所属层、根因、修复和复验。

再加 `/reports/remaining?max_minutes=20`：统计未完成且分钟数不超过阈值的任务；默认 60，允许 0，拒负数。只返回 count/minutes，与分页无关。创建 Zero/0/false、Short/15/false、Long/90/false、Finished/10/true；20 应得 `{"count":2,"minutes":15}`，0 应得 `{"count":1,"minutes":0}`，-1 应为 422。

先尝试，再运行参考（先退出当前服务）：

```bash
uv run --locked python -m uvicorn solutions.remaining_app:app --host 127.0.0.1 --port 8004 --workers 1
```

它明确复用**本实验**的 `app`、`tasks`，从空内存添加路由，不导入别章。用 POST 准备四条数据，并用 HTTP 验证报告。暂停笔记保存目录、入口、最后成功请求及正文、自己的端口/终端、是否已退出、未解决问题和下次命令，始终写明重启会清空内存。

## 文件、正向白名单与未验证边界

同级 **h04-validation-files.json** 明确列出允许显示/下载的源码和文档；禁止递归打包 `.venv`、`__pycache__`、uv 缓存、`.env`/凭证、日志、编辑器文件与个人数据。`.gitignore` 不替代打包 allowlist。共享 loader/ZIP 由集成者处理。SOURCES.md 提供官方依据，VERIFICATION.md 记录实际案例。

同步函数在线程池运行；单工作进程不是锁，读改写与分配 id 不是事务。两个 PATCH 会有丢更新风险，多工作进程持有不同字典。本实验不保证持久化、身份授权、幂等重试、并发负载、跨进程一致性、容量、浏览器 CORS、代理/TLS、生产脱敏或部署；语言阶段辅助函数不提供这些保证。语法检查和模型探针不替代真实 HTTP 验收。
