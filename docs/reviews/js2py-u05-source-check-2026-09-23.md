# L05「异常与调试」资料核对与复审

核对日期：2026-09-23。读者为有成熟前端工程经验、已完成 L00—L04，但未学习导入、文件、类或后端工程的人。本章的语言基线为 CPython 3.13；不把文档核对等同于全部历史教材已实际运行。

## 一手来源与落点

| 核对问题 | 官方来源 | 实际教学落点与边界 |
| --- | --- | --- |
| 解析失败、运行异常与 traceback | [Python 错误与异常教程](https://docs.python.org/3.13/tutorial/errors.html) | 解析前失败没有先前标准输出；四层调用链定位；源表达式与输入原因分开；无异常的错误结果另用控制流排查 |
| 具体异常、首个匹配和处理器作用域 | [try 语句参考](https://docs.python.org/3.13/reference/compound_stmts.html#the-try-statement) | ValueError 不自动捕获 TypeError；宽范围的具体异常仍可吞掉同类内部 bug；else、return/break/continue 路径以执行验证 |
| 异常种类与退出意图 | [内置异常](https://docs.python.org/3.13/library/exceptions.html) | Exception/ValueError/TypeError/LookupError/KeyError 的节选关系；KeyboardInterrupt/SystemExit 不归入 Exception；不要求先学自定义类 |
| raise、重新抛出与原因链 | [raise 参考](https://docs.python.org/3.13/reference/simple_stmts.html#the-raise-statement)、[异常链教程](https://docs.python.org/3.13/tutorial/errors.html#exception-chaining) | 显式拒绝负值、bare raise 保留原始异常和位置；from error 保留原始转换原因，不用 from None 隐藏；底层没有恢复责任则自然传播 |
| finally 的执行与覆盖风险 | [finally 参考](https://docs.python.org/3.13/reference/compound_stmts.html#finally) | 成功、已恢复、未匹配和 return 的实际顺序；finally return 覆盖成功结果及隐藏失败的反例；不声称强杀/断电保证，也不伪装真实资源释放 |
| assert 的移除与输入校验 | [assert 参考](https://docs.python.org/3.13/reference/simple_stmts.html#the-assert-statement)、[-O](https://docs.python.org/3.13/using/cmdline.html#cmdoption-O) | 普通模式下 AssertionError、优化后错误地接受 -5；显式 if/raise 两种模式均有效；必要副作用不放断言 |
| 前端类比边界 | [MDN try...catch](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/try...catch)、[MDN throw](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/throw) | JS catch 通常在内部判断，Python except 可直接按类别；不把 JS 可抛普通值的行为照搬给 Python |

另行核查的边界：异常不会自动撤销已经执行的列表修改；验证在前只保证声明范围的输入错误发生在修改前，不保证修改阶段自身失败也能回滚。独立报告只校验约定的分钟数据，不冒充任意对象、文件导入、HTTP 请求或数据库事务的完整验证。

## 实际 TypeSafe 复审

本轮重新读取官方索引、HTTP API、Choice、Noul 和 citation-check cookbook。本批两次真实请求均提交完整英文对应稿、22 份共享源码、先修能力与 L04/L05/L06/L07/L09 契约，每次 **8 个独立判断**。没有只提交目录，也没有把纯计算或运行验证交给语义评分。

HTTP **200**；请求 `jev-latest`，实际返回 **`jev-1.13.0`**；最终复审 12,448 输入 token / 425 输出 token，用时 1.149 秒；初审 12,382 输入 token / 425 输出 token，用时 1.086 秒。没有开启子智能体，没有将实际 Jev 调用说成 gpt-6-astra，没有增加网站依赖。

| 判断 | 实际结果 |
| --- | --- |
| 未解释必需前置 | P(是) = 0.21 |
| 教学深度 | SUBSTANTIVE，概率 1.00，confidence 1.00 |
| 异常控制流 | ACCURATE_AND_BOUNDED，概率 0.94，confidence 0.91 |
| 恢复责任边界 | EXPLICIT_AND_TESTABLE，概率 1.00，confidence 1.00 |
| 修改与断言边界 | ACCURATE_AND_BOUNDED，概率 1.00，confidence 1.00 |
| 章节范围 | BOUNDED，概率 0.98，confidence 0.97 |
| 独立迁移成立 | P(是) = 0.95 |
| 下一步 | PROCEED_L06，概率 0.82，confidence 0.73 |

下一步的其余分布为 TARGETED_REVIEW 0.11、REVISE_L05 0.07；控制流判断的 MISLEADING 为 0.06。**不把这些剩余概率隐去，也不把材料评分说成真实学习成功率。** Noul 没有单独 confidence。最终决定仍受执行、下载、页面与构建检查约束。

针对非零先修风险，本地逐项检查 repr、type(raw) is not str、except 临时绑定、内置异常关系、原因链与 -O 的首次解释均在要求独立使用之前；没有因此把类定义、导入、文件和测试框架变成隐藏门槛。这是人工材料检查，不是零遗漏证明。

初审的前置风险为 0.24，下一步 PROCEED_L06 概率 0.80、confidence 0.70。随后本地合同复查发现：带提示的 read_minutes 约定拒绝非字符串，却直接调用 int，整数或浮点数可能被接受。因此增加显式普通字符串检查，同步三语说明，并增加 None/整数/浮点数/布尔值/列表/字典的回归。这个具体发现来自本地复查，不能说成 TypeSafe 提供了文字解释。

修正后提交完整材料复审，得到上表的最终结果。第二次调用针对实际材料变更，不是反复请求直到分数变高。初审完整请求与返回保留在 `js2py-u05-initial-review-2026-09-23.json`；其源码指纹是当时快照，不伪装成最终文件的指纹。

实际请求、返回、用量、时间、请求 SHA-256 与 **27 个三语正文/共享源码/README/清单指纹**存于同目录 `js2py-u05-implementation-review-2026-09-23.json`。不保存密钥或鉴权头。

## 复审不能替代的验证

- 三语源码和结果必须一致，所有已声明预期失败都必须实际失败在对应类型与位置；没有异常的反例也必须显示约定的错误行为。
- 除正常输出，还需验证原始异常身份、原因链、finally 的路径、两种优化模式、未知错误传播、行号/顺序、输入不变和重复结果隔离。
- 正文所称的“导入报告”仅处理内存列表。不会因标题包含导入就默认已讲过文件、JSON、模块或数据库。
- 既有 L00—L04 的 AST 限制没有放宽；L04 只更新导航与实施进度，其此前 TypeSafe 记录继续保留历史快照。
- 不声称完成全站所有交互、全部历史示例运行、全面安全审计或真实读者学习效果研究。

实际版本、测试计数、构建和三语页面结果见第七批实施日志。
