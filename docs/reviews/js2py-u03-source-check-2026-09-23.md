# L03 官方资料与审查边界

日期：2026-09-23。对象是「条件、循环与遍历」实际改稿；不是对整本教材、真实学习效果或上线能力的认证。

## 第一手资料核对

本章固定使用 Python 3.13 文档线，不以“最新版本”代替可核验的环境。以下页面通过网络读取并核对相关规则，教学例子自行编写；网页链接不代替正文中的机制解释和实验。

| 核对内容 | 第一手资料 | 本章处理 |
| --- | --- | --- |
| if 分支顺序、for 与 range、break/continue | [Python 控制流教程](https://docs.python.org/3.13/tutorial/controlflow.html) | 分支边界表与每轮状态表；先普通循环，后提前结束与跳过 |
| 缩进语句块、while 检查、for 目标与空迭代 | [复合语句参考](https://docs.python.org/3.13/reference/compound_stmts.html) | 预期缩进失败；空遍历不绑定名称；循环前初始化；明确 while 的推进与终止 |
| 真值与返回操作数、短路 | [Python 内置类型](https://docs.python.org/3.13/library/stdtypes.html#truth-value-testing)、[MDN Truthy](https://developer.mozilla.org/en-US/docs/Glossary/Truthy) | 空列表/字典与 JS 对照；非空 False 文本不等于 bool False；or 默认值不得吞掉合法 0 |
| range 不等于列表或生成器 | [range 类型](https://docs.python.org/3.13/library/stdtypes.html#ranges) | 起止步长、排除终点、方向和零步长；用 list 仅作小范围可视化 |
| 解包、编号与字典 items | [数据结构与遍历技巧](https://docs.python.org/3.13/tutorial/datastructures.html#looping-techniques)、[enumerate](https://docs.python.org/3.13/library/functions.html#enumerate) | 先解包再编号；明确关键字实参；默认字典遍历给键；items 是动态视图而非快照 |
| 列表遍历时改变长度 | [可变序列说明](https://docs.python.org/3.13/library/stdtypes.html#common-sequence-operations) | 连续删除漏项的错误方案；改为构建结果列表；外层新建与内层共享分开说明 |
| 推导式顺序、目标名称边界 | [列表推导式](https://docs.python.org/3.13/tutorial/datastructures.html#list-comprehensions)、[表达式参考](https://docs.python.org/3.13/reference/expressions.html#displays-for-lists-sets-and-dictionaries) | 先给等价普通循环；只引入单层列表推导式；名称不外泄不代表深复制 |

## 实际 TypeSafe 复审

重新读取 TypeSafe 官方索引、HTTP API、Choice、Noul 和 citation-check cookbook。沿用“确定性规则由代码验证，窄语义判断交给 TypeSafe”的流程，没有将服务添加为网站运行依赖。

一次真实请求提交完整英文对应正文、20 个共享 Python 文件、L00—L02 已具备能力和 L03/L04 契约，包含 6 个独立判断。HTTP 200，实际模型 **`jev-1.13.0`**；12,550 输入 token、286 输出 token。没有开启子智能体，没有把 Jev 的调用宣称为 `gpt-6-astra`。

| 判断 | 实际结果 | 限制 |
| --- | --- | --- |
| 是否有未解释的必需先修 | P(是) = 0.15 | 不是零遗漏保证，仍需逐项检查首次使用和验收步骤 |
| 教学深度 | SUBSTANTIVE，概率 1.00、confidence 1.00 | 模型对材料的判断，不等于真实读者研究 |
| 控制流与引用边界 | ACCURATE_AND_BOUNDED，概率 1.00、confidence 1.00 | 只针对当前受限输入、控制流与解释 |
| 章节范围 | BOUNDED，概率 1.00、confidence 1.00 | 不意味着必须一次学完或全书已实现 |
| 独立迁移练习成立 | P(是) = 0.94 | 不是学习者完成练习的成功率 |
| 下一步 | PROCEED_L04，概率 0.94、confidence 0.91 | 先完成运行、内容、构建和页面检查，再进入 L04 |

Noul 没有另造 confidence。完整请求、实际返回、时间与用量、三语正文及共享文件指纹位于 `js2py-u03-implementation-review-2026-09-23.json`，不含密钥或鉴权头。

## 人工检查与确定性验证的职责

- 中文教学主稿与完整英文对应稿人工对照；代码、预期输出和共享来源由三语一致性检查约束，不把 Jev 对英文的判断当成三语翻译认证。
- 普通循环与解包先于 enumerate/items，while 的进展先于 continue 风险，普通筛选先于推导式；每次进入新语法前都有解释。
- 审查前发现筛选与编号示例末尾的固定下标观察会影响空输入实验，已改为：编号脚本先判空；筛选脚本只比较外层身份；内层共享放在独立、明确单项输入的实验中。维护者对完整筛选脚本跑空与非空变式，不截掉不适配的尾部再宣称整份脚本通过。
- 语言范围 AST 检查只允许已学及本章引入的语法；它不能替代教学语义审查。此前 L00—L02 的范围限制没有放宽。
- 脚本与 Python fences 的语法错误、运行异常、正常结果和无异常逻辑错误分开验证；不以编译成功代替正确性。
- `solutions/study_queue.py` 处理的不是任意公众输入；时长类型和记录形状仍有明确契约。维护者测试不会自动变成初学者的先修条件。

具体运行版本、测试数量、实际页面与下载检查见第五批实施日志。L02 仅更新通往新 L03 的链接与进度；其旧 TypeSafe 记录仍是当时正文快照，没有伪装成本次重审。
