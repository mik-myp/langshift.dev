# L01 官方资料核对与验证边界

日期：2026-09-23。对象：已改写的「名称、值与基本运算」，不是全书审查的替代品。

本批使用 Python **3.13 文档线**，不是用“最新 Python”作为模糊前提。实际运行验证使用 CPython **3.13.15**。网络读取官方参考；有些官方说明范围很广，本章只提取当前例子所需的规则，示例与练习为本教材自行编写，没有用参考页代替教学正文。

| 核对问题 | 第一手资料 | 本章落实方式 |
| --- | --- | --- |
| 赋值是重新绑定，不自动克隆或建立响应关系 | [赋值语句](https://docs.python.org/3.13/reference/simple_stmts.html#assignment-statements)、[对象/值/类型](https://docs.python.org/3.13/reference/datamodel.html#objects-values-and-types) | `bindings.py` 与逐行绑定表；避免把不可变整数的行为推广到可变容器 |
| 整数精度、浮点近似、bool 与 int 的关系 | [数值类型](https://docs.python.org/3.13/library/stdtypes.html#numeric-types-int-float-complex)、[浮点教程](https://docs.python.org/3.13/tutorial/floatingpoint.html) | 大整数与浮点分开讨论；不把格式化结果当成精确计算 |
| 除法、负数取整、余数符号 | [算术表达式](https://docs.python.org/3.13/reference/expressions.html#binary-arithmetic-operations)、[MDN remainder](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Remainder) | 正数与负数实验；不把 `//` 叫作截断或必定返回 int |
| JS Number 的安全整数边界 | [MDN MAX_SAFE_INTEGER](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/MAX_SAFE_INTEGER) | Python 与 Node 分别执行对照；说明 JS BigInt 是另一种类型 |
| 字符串不可变、长度与清理方法 | [文本序列](https://docs.python.org/3.13/library/stdtypes.html#text-sequence-type-str)、[字符串入门](https://docs.python.org/3.13/tutorial/introduction.html#text) | 保留原始文本，观察 strip 返回值；ASCII 长度实验不泛化到视觉字符 |
| `int` 的字符串转换与浮点截断不同 | [内置函数](https://docs.python.org/3.13/library/functions.html#int) | `int("3.5")` 与 `int(3.5)` 分开；不以静默丢小数“修复”业务输入 |
| f-string 的显示精度 | [格式规范](https://docs.python.org/3.13/library/string.html#format-specification-mini-language) | 同时输出格式化字符串和原浮点值；说明文字快照不自动更新 |

## TypeSafe 的用途与实际结果

已阅读当日 TypeSafe 的文档索引、HTTP API、Choice、Noul 与 citation-check cookbook，采用“提供实际材料 → 分开判断先修、深度、范围、独立迁移 → 决定下一步”的结构。已发起 **1 次实际请求，5 个独立判断**；返回 `jev-1.13.0`，并非声称 Jev 是 `gpt-6-astra`。没有开启子智能体。

输入是实际完整英文对应稿、12 份 Python 示例、读者背景和 L00/L01/L02 能力边界；不是只把标题目录提交审查。三语代码和预期输出一致性由维护者检查器另行验证。

- 未解释的必需前置能力：P(是) = **0.11**。
- 教学深度：`SUBSTANTIVE`，选项概率 **1.00**，confidence **1.00**。
- 章节范围：`BOUNDED`，选项概率 **1.00**，confidence **0.99**。
- 独立迁移练习成立：P(是) = **0.91**。
- 下一步：`PROCEED_L02`，选项概率 **0.92**，confidence **0.88**。

[Noul 没有独立 confidence 字段](https://docs.typesafe.ai/primitives/noul)，没有把它虚构成一个新的分数。这里的概率不是学习成功率；特别是 0.11 不等于“没有任何遗漏”。仍人工逐项检查练习需要的知识，实际运行源文件，并核对页面与下载。

完整请求、实际响应、时间、用量及源码指纹保存在同目录 `js2py-u01-implementation-review-2026-09-23.json`。记录不含 API 密钥或鉴权头，历史 L00 审查结果保持不变。

## 不夸大本次证据

- 运行成功说明示例在所测解释器上的行为符合预期，不代表读者一定掌握。
- AST 检查限制未教的语法构造，不足以单独证明每个概念都解释到位。
- 没有让真实学习者完成本章并采集学习效果，也没有声称完成所有后续章节。
- 这些脚本没有完整输入校验，不接收公众请求，没有部署为服务。
- 本机运行路径为 macOS；没有新增或声称完成真实 Windows 主机测试。
