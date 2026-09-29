# L04 官方资料与审查边界

日期：2026-09-23。对象是「函数、参数与作用域」的实际改稿，不是对完整课程、真实学习成效或上线能力的认证。

## 第一手资料核对

本章固定在 Python 3.13 文档线，实际环境另见实施日志，不以“最新”代替可复现基线。下列页面已通过网络读取、定位相关说明；教学代码自行编写，链接不代替解释与实践。

| 核对主题 | 第一手来源 | 本章处理 |
| --- | --- | --- |
| def 的执行与函数体的执行 | [函数定义参考](https://docs.python.org/3.13/reference/compound_stmts.html#function-definitions)、[MDN function 声明](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/function#hoisting) | 执行时间线、调用前未定义的 NameError；不把 JS 声明提升推广到全部函数形式 |
| 返回、隐式 None、参数绑定与关键字限制 | [函数教程](https://docs.python.org/3.13/tutorial/controlflow.html#defining-functions)、[return 参考](https://docs.python.org/3.13/reference/simple_stmts.html#the-return-statement) | 返回与输出分开；缺失、重复、错名、仅限关键字的绑定失败；正文区分解析前失败与进入函数前失败 |
| 默认值按 def 执行时求值 | [默认参数](https://docs.python.org/3.13/tutorial/controlflow.html#default-argument-values)、[MDN 默认参数](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/Default_parameters) | 每次执行定义建立默认对象，不是每次调用；真实 Node/Python 对照；省略不等于显式 None/0 |
| 可变默认对象与参数共享 | [Python FAQ](https://docs.python.org/3.13/faq/programming.html#why-are-default-values-shared-between-objects) | 默认列表跨调用共享；局部重绑定不改调用方名称；None 后新建与复制显式标签是两项独立设计 |
| 局部绑定、外层查找与 UnboundLocalError | [执行模型](https://docs.python.org/3.13/reference/executionmodel.html#naming-and-binding)、[作用域教程](https://docs.python.org/3.13/tutorial/classes.html#python-scopes-and-namespaces) | 限定普通函数中的 LEGB 模型；局部未绑定不无条件回退全局；通过参数/返回修复，未要求先学类 |
| 嵌套函数与闭包的绑定读取 | [执行模型中的运行时名称解析](https://docs.python.org/3.13/reference/executionmodel.html#interaction-with-dynamic-features)、[函数定义参考](https://docs.python.org/3.13/reference/compound_stmts.html#function-definitions) | 区分工厂调用与规则调用；返回函数不提前执行；两次工厂建立不同绑定；闭包不是定义时值快照或深复制 |

## 实际 TypeSafe 复审

本轮重新读取官方索引、HTTP API、Choice、Noul 与 citation-check cookbook。只把独立窄语义判断交给 TypeSafe，确定性规则与执行仍由维护工具检查；没有新增网站依赖。

一次真实请求提交完整英文对应稿、23 个共享 Python 文件、L00—L03 已具备能力与 L04/L05 契约，共 **7 个独立判断**。HTTP 200，实际模型 **jev-1.13.0**，13,365 输入 token / 353 输出 token。没有开启子智能体，没有把实际 Jev 调用声称为 gpt-6-astra。

| 判断 | 实际返回 | 限制 |
| --- | --- | --- |
| 存在未解释的必需前置 | P(是) = 0.16 | 不是零遗漏保证，仍需人工检查首次引入和独立验收 |
| 教学深度 | SUBSTANTIVE，概率 1.00、confidence 1.00 | 材料判断，不是真实读者学习实验 |
| 默认值与引用边界 | ACCURATE_AND_BOUNDED，概率 1.00、confidence 1.00 | 当前数据形状与明确的复制政策，不是通用隔离方案 |
| 作用域与闭包 | ACCURATE_AND_BOUNDED，概率 1.00、confidence 1.00 | 限定普通函数与简单配置闭包，没有覆盖全部作用域机制 |
| 章节范围 | BOUNDED，概率 1.00、confidence 1.00 | 不要求一次学完，也不意味着后端主线完成 |
| 独立迁移练习成立 | P(是) = 0.96 | 不是学习者成功率 |
| 下一步 | PROCEED_L05，概率 0.91、confidence 0.87 | 先完成运行、构建、页面等确定性检查 |

Noul 不另造 confidence。请求、返回、时间、用量和 28 个正文/源码/清单指纹保存在 `js2py-u04-implementation-review-2026-09-23.json`，不含密钥或鉴权头。

## 复审之外仍需验证的内容

- 三语可执行代码、输出与共享来源的一致性单独校验，不把英文复审当作翻译质量认证。
- 默认值、显式标签复制、调用次数、输入不变、返回类型、重复调用和交替闭包都需要实际行为测试；只有正确的原始打印结果不能证明独立掌握。
- 函数与推导式语法已有边界检查；不允许学习代码提前使用导入、异常处理、类型注解、装饰器、类或异步。此前章节的 AST 限制未放宽。
- 两份有意错误的源码会触发静态 F821/F823。维护者 lint 仅对对应文件的对应诊断豁免，运行时 NameError/UnboundLocalError 仍是必须通过的预期行为；不是全局关闭检查。
- 没有真实读者实验，没有任意外部输入校验、模块拆分、持久化、并发或服务端；函数工厂也不是已完成依赖注入系统。
- L03 只更新后续链接与实施进度。其原 TypeSafe 记录继续保留为当时正文快照，不伪装成本次重新审查。

实际运行版本、测试数量、页面和下载检查见第六批实施日志。
