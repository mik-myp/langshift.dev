# js2py 教材审查：从企业级前端经验到独立交付 FastAPI 后端

> 当前实施状态（2026-09-28）：39 章材料齐备，33 章本地声明范围验收通过、6 章运维环境待验收。下文仍是其原日期的历史审查，不作为当前缺陷清单；详见[最终记录](/Users/mikmyp/Documents/code-projects/langshift.dev/docs/js2py-remaining-execution.zh-cn.md)。

- 审查日期：2026-09-23。
- 仓库基线：`00d453742c692ad065de91a5e2c7e678665e0157`。
- 状态：历史审查基线与课程设计方案。第 00 章已根据递进复审改为小脚本入门，完整工程后移；部分纠错已分批实施，见[改造记录](/Users/mikmyp/Documents/code-projects/langshift.dev/docs/js2py-implementation-log.zh-cn.md)；下文定位基于本报告记载的仓库提交，不代表改造后的行号或全课程已通过验收。
- 配套文件：[学习路线](/Users/mikmyp/Documents/code-projects/langshift.dev/docs/js2py-learning-path.zh-cn.md)、[贯穿项目与毕业验收](/Users/mikmyp/Documents/code-projects/langshift.dev/docs/js2py-capstone-spec.zh-cn.md)。

## 1. 读者起点与目标

读者能独立搭建前端项目框架，有企业级开发经验，熟悉接口联调、Promise、async/await，了解 TypeScript 基础类型；尚未自行实现后端或数据库。学习时间不固定，接受通过充分练习逐步掌握。

目标应定义为：允许查文档，能够从业务需求出发，独立实现、测试、部署和维护一个中小型后端。首个发布目标是可供受邀用户真实使用的服务，而不是无鉴权演示接口；开放注册的大规模公共产品需要额外验收。

不把以下内容作为先修条件：Express、复杂 TypeScript 类型编程、算法刷题、微服务、Kubernetes、异步 ORM。

## 2. 审查范围、方法与边界

### 本轮完成

1. 对简体中文索引及 00—12 全部模块进行逐章覆盖检查，阅读教学说明、关键代码和练习，检查先修知识与后端目标的衔接。
2. 对三个语言版本的 42 个 MDX 文件做结构、编辑器配置及 Python fenced code 静态盘点；没有逐句核验英文和繁体中文的翻译质量。
3. 使用本机 CPython 3.12.14 对提取出的 Python fenced code 做编译检查，允许顶层 await 的语法解析；这不代表本地脚本或现有网页执行器支持同样的入口。
4. 在全新 Python 命名空间中复验两个类型章节示例，并做 dataclass、闭包语义小实验。
5. 查阅 Python、FastAPI、Pydantic、SQLAlchemy、Alembic、PostgreSQL、Astral 和 OWASP 的一手资料，来源见第 8 节。
6. 运行仓库已有 MDX 检查：678 个文件检查通过。

### 盘点结果

| 版本 | MDX 文件 | PythonEditor | 显式禁用运行 | 默认允许运行 | Python fenced code |
| --- | ---: | ---: | ---: | ---: | ---: |
| 英文 | 14 | 110 | 0 | 110 | 118 |
| 简体中文 | 14 | 111 | 44 | 67 | 119 |
| 繁体中文 | 14 | 111 | 44 | 67 | 119 |

- “默认允许运行”仅指组件属性，**不代表验证通过**。
- 356 个 Python fenced code 中，有两类无法作为 Python 编译的内容，各在三种语言中出现：非法 lambda 参数注解，以及被放入 Python 代码块的 requirements 内容。后者需要拆分文件与语言标记，而不是把合法依赖声明改写成 Python。
- 简体中文模块 01 有 18 个编辑器、英文有 16 个；模块 02 分别为 12 和 13 个。不能仅通过文件存在判断翻译同步。
- 本轮没有穷尽执行每个示例，没有新建完整 FastAPI 环境，没有连接真实数据库，也没有完成部署或安全测试。
- 上一轮已在浏览器验证的异步输出丢失等问题在本报告中标为“前轮复现”；本轮复核相关源码，但没有重复做浏览器全量测试。

MDX 检查通过只说明满足当前检查脚本的表层规则，不证明代码正确或具备完整教学效果。

## 3. 总体判断

**现有教材适合充当语言迁移素材库，不足以单独充当“后端零经验 → 可上线项目”的完整课程。**

优点：有丰富的 JS/Python 对照，基础语法、作用域、类、模块、测试工具和 Pythonic 写法已有可复用内容。无需从零推翻。

主要问题：

1. 读者模型偏差：部分章节默认熟悉 Express，另一些默认熟悉 TypeScript 高级类型。
2. 顺序不合理：完整异步、数据库调用在 HTTP/数据库基础之前；类型与资源管理知识分散在较后章节。
3. 后端工程断层：已有 asyncpg CRUD 示意、sqlite3 项目骨架，**并非完全没有数据库内容**，但缺少 SQL 建模、事务、迁移、权限、接口集成测试和部署恢复的连续教学。
4. 示例契约不明确：语言片段、真实服务、多个文件、配置内容和故意错误，使用近似的运行入口。
5. 练习验收不足：有练习和答案，但没有稳定的从讲解到独立实现的任务梯度。
6. 多语言维护和版本基线缺少统一机制。

本报告中的优先级是教学改造优先级：P0 为示例可靠性与明确错误；P1 为毕业目标必需能力；P2 为体验、补充与扩展。它们不是线上事故等级。

## 4. 逐章处置矩阵

| 原模块 | 已有价值 | 对当前目标的缺口 / 风险 | 建议处置 | 对应验收 |
| --- | --- | --- | --- | --- |
| [索引][MIndex] | 对比学习方法、环境入口 | 写 12 个模块，实际 00—12 共 13 个；普通函数被概括为需要 self；没有后端交付标准 | 重写学习目标、读者前提、必修/选修与环境标记 | 读者能判断每阶段学什么、在哪里运行、怎样算通过 |
| [00 生态与环境][M00] | venv、项目布局、依赖管理 | 工具选择过多；版本示例分散；开发环境介绍没有形成可复现的单一路径 | 一条 uv 主线；保留 pip/venv 原理；其他工具放附录 | 新目录能恢复环境、运行代码与测试，解释解释器/依赖/锁文件 |
| [01 语法][M01] | 基础类型、作用域、函数、异常 | nonlocal 对照表过度概括；语法转换练习不足以训练业务建模 | 合入 10 的高频陷阱、11 的常用写法；补业务边界测试 | 独立实现任务规则，解释空集合、None、可变参数与拷贝 |
| [02 模块][M02] | 导入方式、运行入口、循环导入 | 项目布局与后端应用未串联；配置与代码混合；部分历史版本要求冲突 | 本地多文件实验，明确 cwd、包、模块入口和配置文件 | 从新终端启动多文件项目，独立定位一次导入错误 |
| [03 OOP/函数式][M03] | 类、dataclass、装饰器、推导式 | dataclass 类型安全表述易混淆；一次引入过多高级写法 | 保留常用类/组合/简单装饰器；单例、复杂缓存等放扩展 | 能读懂路由装饰器和模型，不把 dataclass 当外部输入验证器 |
| [04 异步][M04] | coroutine、并发、阻塞陷阱 | 在 HTTP/SQL 基础之前出现服务器、数据库与队列；浏览器入口影响输出；部分示例不自包含 | 拆为“异步语义小节”和“完成同步 API 后的可靠异步调用” | 能解释 coroutine 与 Promise 差别；处理超时、取消与并发上限 |
| [05 质量/测试][M05] | pytest、fixture、参数化、类型检查 | 缺少 API、数据库、权限及配置隔离的测试实践 | 工具与纯函数测试前置；集成测试贯穿后端章节 | 新功能必须有成功、输入错误与权限失败的测试 |
| [06 FastAPI][M06] | 请求参数、BaseModel、Depends 的初步介绍 | 默认会 Express；认证、数据库为占位；缺完整 HTTP、响应模型、路由拆分、配置与生命周期 | 扩展成连续后端主线，不在一个短章里塞完生态 | 从零完成多文件 API，知道数据由谁验证、资源由谁释放 |
| [07 数据/自动化][M07] | 文件、JSON、pathlib、正则 | Pandas 不是首个后端项目的前置条件；文件知识出现偏晚 | 文件/JSON 前置；数据分析保留为选修 | 能处理 UTF-8/缺失文件/非法 JSON；分析报告不阻断毕业 |
| [08 实战][M08] | 短链接、CLI、分析报告的题材 | 短链接核心实现留空；缺迁移、权限、测试与发布验收 | 短链接保留为阶段迁移练习；另设贯穿型协作任务项目 | 在不照抄实现的情况下完成新功能并上线 |
| [09 高级主题][M09] | 生成器、with、装饰器与资源 | 基础资源管理被归入高级主题；“完成系列”与后续章节脱节 | with/yield 移到资源管理；元类与深层协议放附录 | 能解释异常发生时为什么仍要释放文件和 Session |
| [10 常见陷阱][M10] | 很适合 JS 开发者的迁移提醒 | 顺序太晚；不能等写完项目才接触可变默认值等问题 | 融入对应基础章节，原页作为索引与复习 | 为每种高频差异写一个失败用例及修复 |
| [11 Pythonic][M11] | enumerate、解包、推导式、EAFP | 与 03/09 重复；容易把风格偏好理解为绝对规则 | 放进具体代码练习；强调可读性与小范围异常处理 | 重构业务函数但不改变行为，测试保持通过 |
| [12 类型][M12] | 基础注解、容器、TypedDict、Protocol | 有明确语法错误与缺少导入；高级类型负担偏大；Annotated 在末尾扩展而非使用前介绍 | 必需类型前置，复杂泛型选修；区分静态检查与运行时验证 | 会写 API 模型、识别 nullable/缺省，能够解释验证失败 |

## 5. 可定位的问题与修正要求

### A. 已确认的教学与示例问题

| ID / 优先级 | 证据与判断 | 修改方向与完成标准 |
| --- | --- | --- |
| A01 / P0 | [module-12:113](/Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-12-type-annotations.zh-cn.mdx:113) 的 `lambda a: float, b: float: ...` 非法；三语言版本编译均失败 | 使用普通带注解的 def，或给 Callable 变量标注类型；三语言修正且编译通过 |
| A02 / P0 | [module-12:820](/Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-12-type-annotations.zh-cn.mdx:820)、[module-12:877](/Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-12-type-annotations.zh-cn.mdx:877) 的完整 Python 代码块在新命名空间执行均因未导入 TypedDict 报 NameError | 按独立运行契约补全依赖；继续检查后续 Any、TypeVar、Literal、datetime 等名称；不得依赖“之前点过别的示例” |
| A03 / P0 | [module-02:464](/Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-02-module-system.zh-cn.mdx:464) 把 requirements 声明包含在 Python fence 内；英文还默认可运行 | 按真实文件拆出依赖配置并正确标记语言；配置块不送 Python 执行器 |
| A04 / P0 | [module-04:145](/Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-04-async-programming.zh-cn.mdx:145) 创建后台 task；[执行器:424](/Users/mikmyp/Documents/code-projects/langshift.dev/components/python-editor.tsx:424) 同步执行后立即收集输出。前轮浏览器已复现异步结果未进入面板 | 同时修复教材入口和执行生命周期；支持的环境中 await main，而非只把 API 换成 runPythonAsync；正常、异常、取消都测试（S18） |
| A05 / P0 | [执行器:523](/Users/mikmyp/Documents/code-projects/langshift.dev/components/python-editor.tsx:523) 只读取 javascriptCode；模块 12 有四个未禁用的 TS-only 对照 | 明确静态展示或增加真实 TS 转译链；故意类型错误的例子应标静态检查任务，不暗示浏览器能得到 mypy/tsc 诊断 |
| A06 / P0 | [Python stdout 恢复:432](/Users/mikmyp/Documents/code-projects/langshift.dev/components/python-editor.tsx:432) 与 [JS console 恢复:545](/Users/mikmyp/Documents/code-projects/langshift.dev/components/python-editor.tsx:545) 不在 finally；共享解释器使缺少 import 的示例可能被偶然掩盖 | 恢复逻辑进入 finally；每例隔离命名空间、约束并发、提供停止/重置。跨编辑器具体影响还需新增回归测试，不把静态风险写成已全面复现 |
| A07 / P1 | [索引:32](/Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/index.zh-cn.mdx:32) 容易让读者认为普通 def 需要 self；[module-01:314](/Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-01-syntax-comparison.zh-cn.mdx:314) 将闭包使用等同于需要 nonlocal | 区分实例方法与普通函数；nonlocal 用于重绑定外层函数作用域中的名称，读取不需要。已用本地小实验验证读取；见 S01/S02 |
| A08 / P1 | [module-03:446](/Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-03-oop-functional.zh-cn.mdx:446) 的“类型安全”缺少静态/运行时边界 | stdlib dataclass 不自动执行字段运行时类型校验；本地实验允许给 int 字段传入 str。与 Pydantic 分开展示（S03/S05） |
| A09 / P1 | [module-00:489](/Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-00-python-introduction.zh-cn.mdx:489) 与 [module-02:451](/Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-02-module-system.zh-cn.mdx:451) 宣称支持 3.8，其他示例直接使用较新注解写法 | 确定一套解释器基线与锁定依赖；网页 Pyodide 另列版本，不声称两种环境等价。历史写法放兼容性旁注（S17） |
| A10 / P1 | [module-06:10](/Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-06-web-development.zh-cn.mdx:10) 默认熟悉 Node/Express；[module-06:19](/Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-06-web-development.zh-cn.mdx:19) 把服务器/运行时/进程管理概念混在对照里 | 直接从读者熟悉的 fetch 与接口联调讲服务器职责；区分 Python、ASGI 应用、Uvicorn、反向代理（S04/S14） |
| A11 / P1 | [module-04:605](/Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-04-async-programming.zh-cn.mdx:605) 服务器块调用 asyncio.sleep 却未在该块导入 asyncio；[module-06:227](/Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-06-web-development.zh-cn.mdx:227) 使用未给出实现的认证依赖 | 区分完整程序、增量片段、伪代码；完整程序需独立启动并发起请求测试，不能仅做 import 检查 |
| A12 / P1 | [module-08:89](/Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-08-projects.zh-cn.mdx:89) 的数据库存取与重定向仍是占位；缺少完整数据库初始化与验收 | 可保留为挑战题，但必须具备先修教学、接口契约、测试、数据准备和独立参考实现 |
| A13 / P2 | [module-12:887](/Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-12-type-annotations.zh-cn.mdx:887) 用秒级时间戳示意用户 ID，并置于“好的做法” | 明确这不是可靠唯一 ID 生成方案；项目采用数据库主键或合适的 UUID，并使用数据库唯一约束兜底 |
| A14 / P2 | 三语言编辑器数量和可运行设置不同；[繁中生成脚本:20](/Users/mikmyp/Documents/code-projects/langshift.dev/scripts/generate-zh-tw-from-zh-cn.mjs:20) 跳过既存文件 | 引入共享示例 ID、依赖与验收数据；将“文件存在”与“内容同步”分开检查 |

### B. 面向毕业目标必须补齐的能力

以下是课程设计缺口，不表示对应库是 FastAPI 的唯一正确选型。

| ID / 优先级 | 当前情况与必要补充 | 可验证的补齐标准 | 依据 |
| --- | --- | --- | --- |
| B01 / P1 HTTP 与业务契约 | 参数示例已有；缺少服务端视角的资源、状态码、错误语义、请求/响应边界、分页与重复请求处理 | 给一份产品需求，独立写接口契约并解释失败响应；能区分 CORS 与服务端授权 | S04/S16 |
| B02 / P1 类型与验证边界 | BaseModel/Field 有介绍；缺请求/更新/响应模型拆分、缺省与 null、extra 策略、验证与业务规则分工 | PATCH 漏传字段不覆盖原值；非法输入有测试；响应不会输出密码哈希或内部字段 | S05 |
| B03 / P1 SQL 与建模 | asyncpg 示例跳到查询；缺主外键、关系、JOIN、约束、索引和事务的循序练习 | 独立画出表关系、写基本 SQL，证明两步写入失败时全部回滚 | S06/S07/S21 |
| B04 / P1 ORM 与迁移 | 没有完整 ORM/迁移教学链 | 分清 Engine、Session、数据库事务；每请求独立 Session；用迁移升级已有数据，人工检查自动生成结果 | S07/S08 |
| B05 / P1 身份与权限 | 认证为占位，未形成可测试流程 | 登录、过期/伪造凭证、停用用户、跨用户资源访问均有测试；权限检查在后端，不信任前端传来的 owner_id | S09/S10 |
| B06 / P1 应用组织与资源管理 | 模块知识与 FastAPI 应用尚未衔接 | 多文件路由、配置注入、应用级资源初始化/清理、请求级资源释放；避免全局共享 Session | S07/S11/S12/S15 |
| B07 / P1 接口与数据库测试 | pytest 基础已有，没有完整 API 测试闭环 | 独立 PostgreSQL 测试环境；依赖替换后能恢复；外部服务模拟；权限与约束失败路径覆盖；CI 从空库迁移 | S07/S13 |
| B08 / P1 可靠异步 | 示例多但缺逐层验收 | 先会调用/await，再会超时、取消、并发限制；分清同步路由与 async 路由中的阻塞调用；后台任务不作为可靠持久队列 | S16，结合项目约束设计 |
| B09 / P1 交付与运维 | 没有连续部署教学 | 容器、HTTPS、环境配置、启动迁移、日志、健康检查、进程恢复、备份恢复、发布回退与故障排查形成操作手册 | S14/S15，备份恢复为本项目追加验收 |
| B10 / P1 独立迁移能力 | 示例答案不能证明独立开发 | 只给新需求，不给实现步骤；读者自己完成模型、迁移、接口、权限、测试和文档 | 教学设计建议 |

## 6. 教学结构与工具选择原则

1. **必修按依赖排序，不按生态百科排序。** 基础类型、异常、with、简单装饰器先于 FastAPI；SQL 先于 ORM；同步事务先于异步数据库。
2. **不是重新学习前端。** 基础控制流可以快速诊断，重点放 Python 特有语义；不强制编写同等规模的 Express 项目。
3. **不把高级类型编程当门槛。** 必修为基本/容器/联合类型、可空性、Literal、读懂 Annotated 与少量泛型；Protocol 深用法等选修。
4. **收敛工具而非贬低旧工具。** 新路线建议 uv 管环境、Ruff 检查与格式化、pytest + HTTPX 测试；既有 pip/venv/Black 不是错误，只是不需要同时作为多条必学工作流（S19/S20）。
5. **主线只选一种 ORM。** 建议 SQLAlchemy 2.x + Alembic，便于显式学习 Session 和事务。FastAPI 官方数据库教程使用 SQLModel，这不意味着 SQLAlchemy 是官方唯一推荐，更不意味着 SQLModel 不适合生产（S06/S07/S08）。
6. **先正确，再追求并发。** 正常 def 路由可配合同步数据库；异步章节讲实际 I/O 场景。同步辅助函数不会因为被 async 路由调用而自动转入线程池（S16）。
7. **有基础质量要求，但不提前套复杂架构。** 路由、输入输出模型、业务逻辑和数据库职责清楚即可；不强制 Repository/UoW/DDD 的完整抽象层级。
8. **停止只用 canRun 表达运行环境。** 至少区分 browser-python、local-python、local-api、local-node、configuration、illustration、expected-error；明确文件、依赖、入口、输入、输出和检查方法。

## 7. 建议实施批次

### R0：恢复示例可信度

- 修正明确语法错误、缺少导入、错误概括、配置语言标记和虚假运行入口。
- 解决异步输出与异常恢复问题，或在修复前清楚标明本地执行方式。
- 三语言同步关键纠错；把编译检查与编辑器回归测试加入验证。
- 通过标准：正常例子独立可复现；故意错误有类型与预期诊断；无“点击运行却执行了另一种语言”的情况。

### R1：重组 Python 必修主线

- 按学习路线重排知识单元，先不盲目改 URL，避免已有链接失效。
- 把高频陷阱、资源管理、基础类型注解和测试前置；高级内容移到选修。
- 用小型任务管理的纯 Python 规则贯穿，不从大型脚手架开始。

### R2：补齐后端核心

- HTTP/FastAPI/Pydantic → PostgreSQL/SQL → ORM/迁移 → 登录/权限。
- 每个阶段有完整可运行起点、学习任务、验收测试和可单独查看的参考答案。
- 同时建立真实本地示例源文件，不继续在三个 MDX 中各维护一份业务代码。

### R3：测试、发布和独立毕业

- 增加 API/数据库集成测试、受邀用户发布、备份恢复和故障演练。
- 完成一个没有手把手实现的新需求，再进入选修生态。

### R4：内容工程与持续维护

- 为示例增加稳定 ID、适用版本、依赖、环境及验收信息，统一来源后再翻译说明。
- 检查器不能只看标题或组件是否存在，应结合代码编译、隔离执行、类型检查预期、API/数据库测试和多语言对齐。
- 记录官方资料核验日期，升级依赖时重跑项目与示例测试；不把“最新”当永久有效的版本描述。

## 8. 一手资料索引

核验日期均为 2026-09-23。`latest/current` 页面会随上游变化；实施时要配合实际锁定依赖重新验证。来源支撑技术事实，课程顺序、项目范围与验收门槛是本报告的设计建议。

| 编号 | 资料及用途 | 官方地址 |
| --- | --- | --- |
| S01 | Python Tutorial：基础内容覆盖与先修知识 | `https://docs.python.org/3.13/tutorial/` |
| S02 | Python nonlocal：读取与重绑定的区别 | `https://docs.python.org/3.13/reference/simple_stmts.html#the-nonlocal-statement` |
| S03 | stdlib dataclasses：类型注解不等于运行时验证 | `https://docs.python.org/3.13/library/dataclasses.html` |
| S04 | FastAPI Tutorial：主线范围与本地运行 | `https://fastapi.tiangolo.com/tutorial/` |
| S05 | Pydantic Models：验证、转换、模型导出与配置 | `https://docs.pydantic.dev/latest/concepts/models/` |
| S06 | FastAPI SQL Databases：数据库接入与 SQLModel 参照 | `https://fastapi.tiangolo.com/tutorial/sql-databases/` |
| S07 | SQLAlchemy Session Basics：Session 与事务生命周期 | `https://docs.sqlalchemy.org/en/20/orm/session_basics.html` |
| S08 | Alembic Autogenerate：迁移生成与人工复核边界 | `https://alembic.sqlalchemy.org/en/latest/autogenerate.html` |
| S09 | FastAPI Security：密码哈希、JWT 验证与身份获取 | `https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/` |
| S10 | OWASP Authorization：最小权限与逐请求授权检查 | `https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html` |
| S11 | FastAPI Bigger Applications：APIRouter 与多文件组织 | `https://fastapi.tiangolo.com/tutorial/bigger-applications/` |
| S12 | FastAPI Lifespan：应用资源的初始化和清理 | `https://fastapi.tiangolo.com/advanced/events/` |
| S13 | FastAPI Testing：pytest、HTTPX 与 TestClient | `https://fastapi.tiangolo.com/tutorial/testing/` |
| S14 | FastAPI Deployment Concepts：HTTPS、启动、重启与进程 | `https://fastapi.tiangolo.com/deployment/concepts/` |
| S15 | Pydantic Settings：环境配置与类型验证 | `https://docs.pydantic.dev/latest/concepts/pydantic_settings/` |
| S16 | FastAPI async：同步/异步路由、依赖与辅助函数的边界 | `https://fastapi.tiangolo.com/async/` |
| S17 | Python 版本支持状态：选择受支持解释器 | `https://devguide.python.org/versions/` |
| S18 | 当前项目 Pyodide 0.27 JS API：运行接口与异步执行 | `https://pyodide.org/en/0.27.0/usage/api/js-api.html` |
| S19 | uv Projects：环境、项目依赖和锁文件 | `https://docs.astral.sh/uv/guides/projects/` |
| S20 | Ruff Formatter：统一检查/格式化工具选择 | `https://docs.astral.sh/ruff/formatter/` |
| S21 | PostgreSQL Transactions：原子性与回滚 | `https://www.postgresql.org/docs/current/tutorial-transactions.html` |
| S22 | FastAPI Containers：容器交付 | `https://fastapi.tiangolo.com/deployment/docker/` |

## 9. 本轮结论的使用方式

可以据此开始分批改造；不能据此宣称完整课程、推荐依赖组合或毕业项目已经验收。尤其仍需要：

- 对全部“可运行”示例做对应环境下的隔离执行，而非只有语法检查。
- 在确定的 Python/依赖/PostgreSQL 版本下建立可复现项目，再锁定具体版本。
- 为认证、对象级权限、迁移与恢复增加真实测试，不能用文字清单代替执行。
- 对完成后的三语言译文逐段校验。
- 将修订后教材交给符合画像的读者试学，检查是否存在隐含先修知识。

[MIndex]: /Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/index.zh-cn.mdx
[M00]: /Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-00-python-introduction.zh-cn.mdx
[M01]: /Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-01-syntax-comparison.zh-cn.mdx
[M02]: /Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-02-module-system.zh-cn.mdx
[M03]: /Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-03-oop-functional.zh-cn.mdx
[M04]: /Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-04-async-programming.zh-cn.mdx
[M05]: /Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-05-quality-testing-typing.zh-cn.mdx
[M06]: /Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-06-web-development.zh-cn.mdx
[M07]: /Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-07-data-automation.zh-cn.mdx
[M08]: /Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-08-projects.zh-cn.mdx
[M09]: /Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-09-advanced-topics.zh-cn.mdx
[M10]: /Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-10-common-pitfalls.zh-cn.mdx
[M11]: /Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-11-pythonic-code.zh-cn.mdx
[M12]: /Users/mikmyp/Documents/code-projects/langshift.dev/content/docs/js2py/module-12-type-annotations.zh-cn.mdx
