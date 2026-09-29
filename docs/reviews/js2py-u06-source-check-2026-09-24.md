# L06「模块与标准库」资料核对与复审

核对日期：2026-09-24。读者已经完成 L00—L05，尚未学习文件读写、项目环境、测试框架或服务端。语言基线 CPython 3.13，实际终端验收版本为 **3.13.15**；这是实测版本而非“最新版本”承诺。

## 一手来源与教学落点

| 核对问题 | 来源 | 正文落点与限制 |
| --- | --- | --- |
| 模块命名空间、import/from/as | [Python 模块教程](https://docs.python.org/3.13/tutorial/modules.html)、[import 语句](https://docs.python.org/3.13/reference/simple_stmts.html#the-import-statement) | 加载模块与在调用方绑定名称分开；from 不按行选择执行、不自动绑定源模块名称；别名不改原实现 |
| 顶层执行与缓存 | [导入系统](https://docs.python.org/3.13/reference/import.html)、[编译文件缓存](https://docs.python.org/3.13/tutorial/modules.html#compiled-python-files) | 新进程重新初始化；普通同名导入复用内存模块对象；不把文件身份等同于导入名称，也不把 pyc 解释为跨进程业务状态 |
| 直接导入的绑定、函数定义环境 | [模块教程](https://docs.python.org/3.13/tutorial/modules.html#more-on-modules)、[MDN ESM import](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/import) | Python from 不产生 ESM live binding，也不深复制对象；绑定变更与列表修改分别实验；导入函数读取其定义模块的全局名称 |
| main 入口与守卫 | [顶层执行环境](https://docs.python.org/3.13/library/__main__.html) | main 不是自动调用约定；守卫不阻止其他顶层执行；准备数据和业务调用一起放进入口，不能只保护最后的打印 |
| 工作目录、脚本目录、模块搜索 | [搜索路径初始化](https://docs.python.org/3.13/library/sys_path_init.html)、[命令行](https://docs.python.org/3.13/using/cmdline.html)、[os.getcwd](https://docs.python.org/3.13/library/os.html#os.getcwd) | 三者分别观察；正常文件执行与 -m 的搜索起点不同；-m 使用模块名而非 .py 路径；不混淆 sys.path 与 Shell PATH；不引入路径补丁 |
| 普通包、相对导入和初始化 | [包教程](https://docs.python.org/3.13/tutorial/modules.html#packages)、[导入系统](https://docs.python.org/3.13/reference/import.html) | 明确本章用普通包，不声称所有包都必须有 __init__.py；包初始化会执行；相对点指包上下文，不指 cwd；直接包内文件启动与 -m 分别验收 |
| 少量标准库的真实契约 | [math.ceil](https://docs.python.org/3.13/library/math.html#math.ceil)、[statistics.mean](https://docs.python.org/3.13/library/statistics.html#statistics.mean) | 上取整、算术均值；空数据没有均值，不伪装成零；标准库同样需要明确输入与错误边界 |
| 缺模块、缺名称、同名遮蔽、循环 | [导入系统](https://docs.python.org/3.13/reference/import.html)、实际 CPython 3.13.15 子进程 | 观察真实来源与 traceback；循环导入尚未建立的名称和模块根本不存在是不同问题；修复依赖方向，不靠改 import 顺序碰运气 |

以上均读取了正文相关部分，不是只添加链接。JavaScript 对照另用真实 Node `.mjs` 实验验证 live binding（20 → 40）及导入方重新赋值的 TypeError；不把结论泛化到所有 CommonJS/打包器转换。

## 实跑暴露的诊断差异与修订

最初的维护测试期待循环导入的消息包含 `partially initialized module`。本机默认 Python 3.12 检查通过，但正文指定的 **CPython 3.13.15** 实跑给出 `ImportError: cannot import name 'total_minutes' from 'cycle_a'`，并附带考虑重命名文件的建议。

没有为了通过测试就删除循环检查，也没有把建议当根因。修订后三语第 11 节展示缩略但真实的三帧 traceback，解释 `run → A → B → 尚未完成的 A`，说明诊断建议与版本相关，必须回到源代码确认。维护测试同时验证异常类别、所缺名称和三帧顺序 `run.py → cycle_a.py → cycle_b.py`，不再绑定某个提示措辞。

另外修复了测试路径归一化：macOS 临时目录的 `/var` 与 `/private/var` 是同一实际目录的两种路径表达。先归一化解析后的真实路径，再处理原路径；不修改教学程序的工作目录语义，不用宽泛忽略输出来绕过检查。

## 实际 TypeSafe 审查

重新读取 TypeSafe 的官方索引、HTTP API、Choice、Noul 和 citation-check cookbook。两次真实请求都包含**完整英文正文、37 份 Python 源码、下载 README、读者与先修契约**，不是只传目录或教学愿景。维护测试不作为读者先修内容。

- 初审：8 个判断，HTTP 200，输入 20,229 token / 输出 415 token，1.430 秒。
- 修订稿复审：9 个判断，HTTP 200，输入 20,696 token / 输出 482 token，1.253 秒。
- 请求模型 `jev-latest`，实际返回 **`jev-1.13.0`**。没有开启子智能体，也没有把 Jev HTTP 判定描述成 gpt-6-astra 调用。
- 凭据仅通过临时进程隐藏输入使用，没有写入仓库、下载包或审查证据。

| 修订稿判断 | 实际结果 |
| --- | --- |
| 未解释的必需先修知识 | P(是) = 0.17 |
| 教学深度 | SUBSTANTIVE，概率 1.00，confidence 1.00 |
| 导入、绑定与缓存 | ACCURATE_AND_BOUNDED，概率 1.00，confidence 0.99 |
| 入口与运行上下文 | ACCURATE_AND_BOUNDED，概率 1.00，confidence 1.00 |
| 独立作业契约 | COHERENT_AND_TESTABLE，概率 0.99，confidence 0.98 |
| 章节范围 | BOUNDED，概率 0.99，confidence 0.99 |
| 独立迁移成立 | P(是) = 0.97 |
| 修订后的错误诊断 | ACCURATE_AND_ACTIONABLE，概率 1.00，confidence 0.99 |
| 下一步 | PROCEED_L07，概率 0.83，confidence 0.75 |

下一步剩余分布为 TARGETED_REVIEW 0.12、REVISE_L06 0.05；独立作业仍有 CONTRADICTORY 0.01，范围判断有 TARGETED_REVIEW 0.01。**没有隐去这些不确定性。** Noul 没有额外 confidence；Choice 的 confidence 不是教材正确率，更不是读者完成后的成功率。

初审的先修风险为 0.18，下一步 PROCEED_L07 概率 0.92、confidence 0.89。实际运行发现诊断措辞问题后才修订并复审，最终评分反而降低；完整保留初审，不以多次重试挑选最高分。选择遵循“验证通过后进入 L07”的有条件建议，不将概率当作自动免检通行证。

### 针对非零先修风险的本地逐项核查

| 独立作业依赖 | 已有解释位置 |
| --- | --- |
| 名称、引用、容器、遍历、函数、异常与原因链 | L01—L05；L06 不要求重新从框架例子猜语法 |
| 模块属性、标准库与具名导入 | 第 1—4 节，先解释模块命名空间，再要求调用 |
| 共享修改、函数所属全局名称、普通导入缓存 | 第 5 节；不要求读者操作 sys.modules |
| `__name__`、main 定义与明确调用 | 第 6 节；先对比导入和直接运行，再做入口修复 |
| cwd、`__file__`、sys.path 和 `-m` | 第 7 节，三个实际位置输出之后才引入包 |
| `__init__.py`、文档字符串、点分名称、相对导入 | 第 8 节，全组文件与两类入口输出完整呈现 |
| 错误上下文、遮蔽、循环 | 第 9—11 节先失败再定位；第 12 节才要求独立诊断 |
| 严格类型、每项阈值、返回数据隔离 | 已有 L01/L02/L04/L05 基础，第 12 节再次明确契约与变式 |

文件读取、JSON、依赖声明、安装/发布、类、装饰器和 pytest 都不进入必做作业。这里是人工材料核查，不是“零遗漏”证明；仍需要真实读者反馈校准教学效果。

## 确定性验证与范围

- 37 份 Python 源码 + 三语 README，严格白名单生成 ZIP；三语正文 37 个共享文件引用、命令和输出围栏逐项一致。
- CPython 3.13.15 / uv 实跑 **28 个入口场景，含 8 个预期失败**。不把辅助模块当独立程序，不用 `-I` 破坏本章需要的本地搜索路径。
- 新增 **18 项 Python unittest**：包含 340 个计划器组合、24 个顺序排列、类型/原因链、未知错误传播、结果隔离、缓存边界、遮蔽修复、依赖方向和空目录重建。
- 将入口的 main 临时植入必定失败的哨兵：导入不得触发，明确启动必须触发；与已知顶层业务语句的结构检查结合，不只凭“没有打印”推定无副作用。
- 下载包置于要求 Python >=99 且锁文件无效的外层项目中，实际 `--no-project` 命令仍能执行；原源码和外层文件字节不变，只允许与源码对应的 `__pycache__/*.pyc`。不错误要求正常导入后目录完全无新文件。
- 从真正的空目录恢复独立参考包，验证导入、-m、错误直接启动及 budget=40 变式。
- 累计 **102 项 Python unittest、7 项 Node 测试**；42 篇 js2py MDX / 231 个 Python 围栏语法检查、39 个既有类型声明冒烟片段、8 个确定性 ZIP 检查通过。
- L00—L05 实際命令回归、保留工程 6 个基线 / 4 个预期练习失败 / 10 个参考答案用例、旧锁文件拒绝和空目录复现通过。
- 全站 678 篇 MDX、TypeScript、ESLint、生产构建通过。原有两处 Hook 依赖警告、Code Hike 空语言、工作区根推断、静态导出 headers/API 与 next lint 弃用提示仍在；不擅自修无关配置。
- 三语浏览器均在 **1280×900** 验证标题/侧栏、14 节、三个答案默认折叠并可实际打开、37 份展示源码与源文件逐字一致、HTTP ZIP 字节相同、无页面级横向溢出。实际查看顶部、绑定实验与展开答案共 **9 张截图**；代码长行保留块内滚动。不声称已验证移动端、全站所有交互或零浏览器联网请求。

对应证据：`js2py-u06-initial-review-2026-09-24.json`、`js2py-u06-implementation-review-2026-09-24.json`、`js2py-u06-browser-qa-2026-09-24.json`。最终复审记录绑定 64 个源码/配置/下载/归档文件哈希；初审记录绑定当时实际提交快照，不用最终文件冒充旧快照。

ZIP SHA-256：`6e4193b33ed884e72af3c00ef72b5dc41d5affa4d559e4d9514e1f593d954eb8`。

## 下一步边界

目前仅 L00—L06 已落实，39 个逻辑章节中仍有 32 个待实施。下一章 L07 讲文件、编码、路径、JSON 序列化、缺失/损坏文件和 with 使用；不提前实现自定义上下文协议、完整环境工程或 FastAPI。
