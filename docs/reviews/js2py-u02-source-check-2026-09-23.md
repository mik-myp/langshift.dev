# L02 官方资料与审查边界

日期：2026-09-23。审查对象是「容器、引用与修改」的实际改稿，不是对整本教材或真实学习效果的认证。

## 第一手资料核对

本章固定在 Python 3.13 文档线，实际测试使用 CPython 3.13.15，不以“最新版本”替代可核验的环境。以下页面已通过网络读取并核对相关规则；教材例子与练习自行编写，未用文档链接代替教学正文。

| 问题 | 原始参考 | 教材处理 |
| --- | --- | --- |
| 列表方法的修改与返回值 | [Python 数据结构教程](https://docs.python.org/3.13/tutorial/datastructures.html#more-on-lists)、[MDN Array.push](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/push) | 先区分 append 的原地修改/None 与 pop 的移除/返回，再复现错误重绑定 |
| 赋值不自动复制、浅复制的内部共享 | [copy 文档](https://docs.python.org/3.13/library/copy.html) | 别名、平面复制、嵌套共享与指定层级隔离分别实验；不把修复推广为通用深复制 |
| 重复列表的共享引用 | [Python FAQ：多维列表](https://docs.python.org/3.13/faq/programming.html#how-do-i-create-a-multidimensional-list) | `[[]] * 2` 与 `[[], []]` 对照；不提前依赖循环或推导式 |
| 字典顺序、键、缺失与默认值 | [字典类型](https://docs.python.org/3.13/library/stdtypes.html#mapping-types-dict) | get 不插入字段；缺失与已有 None 分开；不把顺序误解为位置下标 |
| 元组不可变的层级 | [元组教程](https://docs.python.org/3.13/tutorial/datastructures.html#tuples-and-sequences) | 固定槽位与槽位指向的可变列表分开，配套赋值失败实验 |
| 可哈希不等于简单的“不可变”标签 | [hashable 术语](https://docs.python.org/3.13/glossary.html#term-hashable)、[集合类型](https://docs.python.org/3.13/library/stdtypes.html#set-types-set-frozenset) | 说明字符串标签合法、列表成员失败，以及包含列表的元组也不可哈希 |
| 集合显示顺序与排序结果类型 | [sorted](https://docs.python.org/3.13/library/functions.html#sorted) | 排序生成列表后打印，不能据此认为原集合有位置顺序；多组 hash seed 验证输出 |
| JS 数组/集合的身份语义 | [MDN Strict equality](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Strict_equality)、[MDN Set](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Set) | 明确 Python 容器内容比较与 JS 对象严格相等不是同一操作，不把 JS Set 容纳数组的规则搬到 Python |

## 实际 TypeSafe 复审

沿用“事实与执行由代码核验，语义判断交给 TypeSafe”的流程。本次重新读取了官方文档索引、HTTP API、Choice 与 Noul 的当前说明，没有把 TypeSafe 安装成教材网站依赖。

一次实际请求提交完整英文对应正文、18 个共享 Python 文件、已完成的 L00/L01 能力与 L02/L03 契约，共 **6 个独立判断**；模型实际返回 **`jev-1.13.0`**，HTTP 200，12,032 输入 token / 294 输出 token。没有开启子智能体，也没有把 Jev 宣称为 `gpt-6-astra`。

| 判断 | 实际返回 | 解读限制 |
| --- | --- | --- |
| 存在未解释的必需前置能力 | P(是) = 0.16 | 不是零遗漏保证；仍人工逐项检查必修任务 |
| 教学深度 | `SUBSTANTIVE`，概率 1.00、confidence 1.00 | 是模型对材料的判断，不是读者实验结果 |
| 复制边界解释 | `ACCURATE_AND_BOUNDED`，概率 1.00、confidence 1.00 | 只针对当前解释及限定的数据形状 |
| 章节范围 | `BOUNDED`，概率 1.00、confidence 1.00 | 不代表全书已经完成 |
| 独立迁移练习成立 | P(是) = 0.91 | 不是学习者完成练习的成功率 |
| 下一步 | `PROCEED_L03`，概率 0.91、confidence 0.87 | 仍须通过运行、内容、构建与页面检查 |

Noul 没有另造 confidence 值。完整请求、实际返回、时间、用量和三语正文指纹在 `js2py-u02-implementation-review-2026-09-23.json`，不含 API 密钥或鉴权头。

## 本次审查不覆盖什么

- 没有组织真实读者实验，也不能仅凭模型概率或测试通过宣称教材完美。
- AST 检查约束语法范围，但不能替代概念解释的逐段检查。
- 所有脚本只在本地处理源码给定数据，没有公众输入校验、持久化、数据库事务或并发隔离。
- macOS 上实测了命令与下载；没有新增真实 Windows 主机验证。
- L01 只更新了通往新 L02 的导航/迁移说明，原 L00/L01 的 TypeSafe 记录保留为当时材料的历史证据，没有伪装成本次重新审查。
