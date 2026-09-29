# L07「文件、JSON 与资源使用」资料核对与复审

核对日期：2026-09-24。读者完成 L00—L06，仍不要求依赖工程、测试框架、类或服务端实践。语言基线为 CPython 3.13，实际终端验收使用 **3.13.15**；这是实测版本，不是最新版本声明。

## 一手资料与教学落点

| 核对问题 | 一手来源 | 正文中的机制与边界 |
| --- | --- | --- |
| 文本/二进制读取、位置、行与关闭 | [Python 文件教程](https://docs.python.org/3.13/tutorial/inputoutput.html#reading-and-writing-files)、[I/O](https://docs.python.org/3.13/library/io.html) | 全量读取会占用相应内存；读取推进位置；EOF 与重新打开不同；去掉行尾不能误删有效空白；已读文本不因关闭而消失 |
| 路径、当前目录和目录创建 | [pathlib](https://docs.python.org/3.13/library/pathlib.html) | Path 对象不是已打开的资源；相对路径依赖 cwd，文件锚点依赖 __file__；mkdir 是明确动作；路径拼接不是任意用户路径的安全沙箱 |
| 编码、字符、字节和换行 | [Unicode HOWTO](https://docs.python.org/3.13/howto/unicode.html)、[open](https://docs.python.org/3.13/library/functions.html#open) | 字符串长度与 UTF-8 字节数不同；解码失败不等于 JSON 语法错误；声明编码不会修复错误字节；默认换行转换与显式 LF 分开解释 |
| r/w/a/x 与截断 | [open](https://docs.python.org/3.13/library/functions.html#open) | w 在成功打开时截断；a 不会自动合并 JSON；x 拒绝已存在目标；普通文件写入不会创建缺失父目录 |
| with 取得/退出与异常 | [with 语句](https://docs.python.org/3.13/reference/compound_stmts.html#the-with-statement)、[I/O](https://docs.python.org/3.13/library/io.html) | 正常、return、块内异常都释放已取得的文件；打开失败时没有文件可交给主体；关闭不是回滚，也不是抗崩溃持久化承诺 |
| 文件错误与恢复职责 | [内置异常](https://docs.python.org/3.13/library/exceptions.html) | 缺文件、缺父目录、目录类型不符、权限、解码错误分层诊断；不预先用 exists 代替操作；未知 I/O 错误不伪装成空数据 |
| JSON 转换、文档边界和验证 | [Python JSON](https://docs.python.org/3.13/library/json.html)、[RFC 8259](https://www.rfc-editor.org/rfc/rfc8259) | dumps/loads 与 dump/load 的输入和资源责任不同；元组/键转换、set 拒绝、NaN 和重复键有明确限制；解析成功不保证业务形状；两次 dump 不构成单文档更新 |
| JavaScript 对照 | [MDN JSON.stringify](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON/stringify) | 实际执行三语正文中的 JS 源码；验证 Unicode 输出与 JSON.stringify(NaN) 为 null，不把 Python 默认 JSON 行为等同于 JS |

上述页面的相关正文已读取；本轮临时工作目录还保留抓取及文本提取结果。正文列出来源，但不要求初学者先阅读完整语言参考才做练习。

## 实际 TypeSafe 请求与解释

已读取 TypeSafe 官方索引、HTTP API、Choice、Noul 和 citation-check cookbook。本次只有 **一次真实语义审查**，提交完整英文正文、31 份实际 Python 源码、六份输入素材（无效 UTF-8 的原始单字节表示为 hex `ff`）、三语下载 README、读者/先修契约与当时真实的验证进度，不能冒充当时尚未完成的构建和浏览器检查。

- 请求模型：`jev-latest`；实际服务返回 **`jev-1.13.0`**，不是 `gpt-6-astra` 子智能体。本轮未启用任何子智能体。
- 10 个独立判断，HTTP 200，耗时 1.513 秒；输入 20,461 token / 输出 547 token。
- 教学深度选择 SUBSTANTIVE；路径/编码、资源释放、写入安全、JSON/校验均选择 ACCURATE_AND_BOUNDED，各选项概率 1.00。
- 独立契约选择 COHERENT_AND_TESTABLE，概率 0.87、confidence 0.83；CONTRADICTORY 仍占 0.11，UNDERSPECIFIED 与 UNCERTAIN 各占 0.01，不能忽略这些分支。
- 隐藏先修 Noul `P(yes)=0.21`；独立迁移 Noul `P(yes)=0.97`。Noul 没有另一个 confidence。
- 下一步选择 **PROCEED_L08**，概率 0.91、confidence 0.86；TARGETED_REVIEW 0.06，REVISE_L07 0.03。该问题明确以确定性检查实际通过为前提。

这些是模型的分布，不是教材正确率、学习成功率或“完美教材”证明。没有为提高分数重发未改变的材料。维护程序、测试框架和故障注入不属于学习者先修要求。

## 对不确定分支进行本地核查

| 核查点 | 前置解释和实际证据 |
| --- | --- |
| Path、路径运算和文件锚点 | 第 2 节在操作文件之前逐项解释，分别从实验根目录和 fixtures 目录执行，定位同一源文件输入；并未要求定义类或实现运算符协议 |
| with、流、closed、EOF | 第 3—4 节先建立使用模型，第 7 节再展开正常、return、异常及取得失败；已有 L05 finally 基础；真正的流在成功、解码/解析/校验失败后均检查 closed |
| bytes、编码和 newline | 第 5—6 节解释后才要求诊断；UTF-8 字节、单字节 ff、字符计数与写入字节数有实际断言，不靠乱码截图猜测 |
| 严格业务类型与返回对象 | 容器、引用、type、遍历与函数已在 L01—L05；第 12—13 节明确 exact keys、普通 int、拒绝 bool、保留标题与顺序、空数组和零、结果与输入隔离 |
| 首次、重复和空数据 | 首次初始化由 app 负责，load_tasks 本身传播缺失；空数组不是缺失。新进程逐次运行，35→36 输入变式真实改变汇总，空数组保持为空 |
| 缺失父目录与缺文件 | 第 8 节区分缺失组件；app 在读取前创建自己锚定的父目录。修复练习的演示调用方也先创建固定 scratch 父目录；其 load_or_empty 是该练习的恢复策略，不是任意路径初始化服务。存储库对缺父目录、权限和未知 I/O 错误继续传播 |
| 坏数据与写入责任 | UTF-8、JSON 语法、根/行/字段错误分别运行；旧字节保持不变。保存前验证/序列化失败时没有打开目标；写入途中注入失败则明确观测到已发生部分写入，证明没有原子性保证 |
| 模块入口与不同 cwd | 沿用 L06 main 守卫与普通包；导入探针不创建目录或读写数据，入口哨兵验证导入与运行有别；外层 run_store.py 可从其他 cwd 启动，直接包内 app.py 的失败也明确列出 |
| 练习与答案一致性 | 空目录重建六个独立文件，不借用下载中的包；33 个完整命令场景、十个生成文件逐字节断言，三语 32 份展示内容、所有命令/输出围栏和中文数据字面量一致 |

以上检查没有发现需要修改本次受审英文/源码的实质矛盾，因此保留原始请求与响应，未以新文件冒充旧快照。材料核查仍不能代替真实读者使用反馈。

## 确定性验证

- 新增 **20 项 Python unittest**；包括 32 种有效字段组合、6 种顺序排列、无效根/行/字段、输入与返回对象隔离、已取得的真实流释放、受控权限/未知 I/O/准备失败、部分写入失败及导入副作用防护。
- CPython 3.13.15 / uv 实跑 **33 个顺序场景，8 个预期失败**；初次和再次运行的输出不同有明确前提，不为重复创建 x 模式文件偷偷清理状态。
- 38 条 ZIP 白名单（31 Python、6 输入、1 README）字节不变；只允许十个确切输出和与源码对应的字节码缓存。无 .venv、新锁文件、意外父目录输出。所有 destructive 演示都在固定 `_output/`，不修改 fixtures。
- 下载放在 Python >=99、无效锁文件的父项目下，实际 --no-project 忽略父工程并保持配置原字节。独立目录验证导入、首次、再次、不同 cwd、修改输入、空数组和损坏文件拒绝覆盖。
- 累计 **122 项 Python unittest、8 项 Node 测试**通过；L00—L07 实际集成回归通过。保留历史工程的 6 基线、4 预期练习失败、10 参考答案用例、陈旧锁文件拒绝和空目录重建均通过。
- 42 篇 js2py MDX、216 个 Python 围栏语法、39 个既有类型声明冒烟进程、L00—L07 三语共享源码/输出一致性、9 个确定性 ZIP 通过。语法检查不等于全书所有示例都已验收。
- 新增内容 Ruff 检查/格式检查通过；全站 678 篇 MDX、TypeScript、ESLint 和生产构建通过。保留原有两处 Hook 依赖、Code Hike 空语言、工作区根推断、静态导出 headers/API 与 next lint 弃用警告，未修改无关配置。
- 三语实际浏览器各验收 1280×900 桌面视口：标题/侧栏、15 节、三个答案默认折叠且均可点击展开、32 份展示源码逐字相等（31 Python + 1 JSON）、下载 HTTP 字节一致、无页面级横向溢出，代码前景色 `rgb(201, 209, 217)`。已实际查看顶部、资源释放代码、展开独立答案共 9 张截图；长行在代码块内滚动。不声称覆盖移动端、全站交互或零浏览器联网请求。
- 浏览器维护脚本第一次把预测答案误当作包含 False 的输出，因而正确中止；检查实际展开内容后，改为断言该答案真实解释中的 None 和 JSON 数字文本示例。未修改教材去迎合错误断言，也未删除答案展开检查；随后三语全部通过。

证据文件：`js2py-u07-implementation-review-2026-09-24.json`、`js2py-u07-browser-qa-2026-09-24.json`。英文、所有 Python、README 与六份原始输入均和真实请求逐字节匹配；其他哈希只绑定确定性检查的文件，不冒充语义服务读过的内容。

## 下一步与限制

目前 **L00—L07 已实现；39 个逻辑章节中仍有 31 个待实施**。下一批 L08「环境与依赖管理」，在已有模块/文件基础上再解释解释器定位、标准库与第三方包、隔离、声明、锁定和环境恢复。L07 不是生产存储、数据库、事务、并发写入或任意上传处理方案；自定义资源协议仍放 L14，不提前跳入 FastAPI。
