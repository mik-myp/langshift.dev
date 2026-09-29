# L08—L10：资料核对、真实复核与阶段验收

日期：2026-09-28。用户授权继续全部剩余章节，不再逐章确认；本记录只验收本轮实际实现的 L08—L10，不把该授权变成“剩余全部已完成”。当前完成 L00—L10，共 11/39 章，后续 28 章仍待实施。

## 一、资料与机制落点

| 主题 | 一手资料 | 教学与验收落点 |
| --- | --- | --- |
| 项目文件、声明与直接/间接依赖 | [uv 项目指南](https://docs.astral.sh/uv/guides/projects/)、[依赖管理](https://docs.astral.sh/uv/concepts/projects/dependencies/) | 四种参与者、四类文件的职责；非发布应用；TOML 当前用法先解释后使用；依赖声明不等于 import |
| 锁与环境一致性 | [uv 同步](https://docs.astral.sh/uv/concepts/projects/sync/) | locked 不同于 frozen；uv run 默认非精确、uv sync 默认精确。实际安装额外 packaging，观察 run 保留而 sync 移除；不把一次成功当作没有隐含依赖 |
| 解释器与包来源 | [uv Python 选择](https://docs.astral.sh/uv/concepts/python-versions/)、[venv](https://docs.python.org/3.13/library/venv.html)、[发行包和导入包](https://packaging.python.org/en/latest/discussions/distribution-package-vs-import-package/) | sys.executable/prefix 与发行元数据、模块 __file__ 分别观察；实际缺声明、同名遮蔽、陈旧锁分层诊断 |
| 外部函数的最小契约 | [humanize filesize](https://humanize.readthedocs.io/en/stable/filesize/) | 1536→1.5 KiB、2048→2.0 KiB、0→0 Bytes；显示字符串不参与原始字节计算；业务校验由本地函数完成 |
| 测试机制与发现 | [pytest 入门](https://docs.pytest.org/en/8.4.x/getting-started.html)、[项目实践](https://docs.pytest.org/en/8.4.x/explanation/goodpractices.html)、[导入路径](https://docs.pytest.org/en/8.4.x/explanation/pythonpath.html) | 先普通 assert，再引入发现/执行；testpaths 隔离故意错误；collect-only 与执行不同；不使用 fixture、装饰器、类或路径补丁 |
| 断言与失败报告 | [pytest 断言](https://docs.pytest.org/en/8.4.x/how-to/assert.html)、[退出码](https://docs.pytest.org/en/8.4.x/reference/exit-codes.html) | raises 的异常类别/子类与消息责任；执行失败 1、收集错误 2、没有测试 5 均实际复现；函数对象真值造成的假绿明确标为反例 |
| 临时资源与文件验收 | [TemporaryDirectory](https://docs.python.org/3.13/library/tempfile.html#tempfile.TemporaryDirectory)、[pathlib](https://docs.python.org/3.13/library/pathlib.html)、[JSON](https://docs.python.org/3.13/library/json.html) | 在使用前解释临时目录、with 的取得/清理、路径参数及测试所有权；成功往返之外检查保存前拒绝与损坏输入的原始字节 |
| 导入与多文件 | [Python 模块](https://docs.python.org/3.13/tutorial/modules.html) | 复用 L06；main 守卫、独立导入探针、外层入口、显式 --project 与 cwd 分开验收 |

官方页面已获取并读取相关正文，不只是补链接。Python JSON 页面一次读取发生 TLS EOF，随后正常重取成功，没有关闭证书验证。Python 3.13 是课程基线；实际版本 CPython 3.13.15、uv 0.12.13、humanize 4.13.0、pytest 8.4.2，不声称它们是最新版本或已通过长期安全认证。

## 二、真实 TypeSafe 审查

读取当日 TypeSafe 官方索引、HTTP API、Choice、Noul 与 citation-check。三个独立真实请求分别包含对应**完整英文正文、全部下载文件（包括源码、测试、配置、锁和 README）、读者、先修契约与当时真实验证状态**。提交时明确说明完整构建/浏览器尚未结束，没有事后回填请求去冒充当时已全部通过。

| 章节 | 实际模型 | HTTP | 输入/输出 token | 耗时 | next_action |
| --- | --- | --- | --- | --- | --- |
| L08 | jev-1.13.0 | 200 | 10,935 / 341 | 1.068 秒 | PROCEED 0.89；confidence 0.85 |
| L09 | jev-1.13.0 | 200 | 14,125 / 341 | 1.418 秒 | PROCEED 0.91；confidence 0.86 |
| L10 | jev-1.13.0 | 200 | 13,410 / 341 | 1.523 秒 | PROCEED 0.89；confidence 0.84 |

每次有七个独立判断。实际服务是 TypeSafe System One / Jev，不是 gpt-6-astra 子智能体；未开启任何子智能体。概率是模型分布，不是教材正确率、学习成功率或“完美”认证；Noul 没有额外 confidence。

没有只保留有利分支：

- 隐藏先修 P(yes)：L08 0.28、L09 0.33、L10 0.33。
- L08 独立契约 COHERENT_AND_TESTABLE 0.82，但 CONTRADICTORY 仍为 0.15；技术机制 NECESSARY_GAP 为 0.06。
- L09 技术机制 ACCURATE_AND_BOUNDED 0.81，但 NECESSARY_GAP 为 0.14、MATERIAL_ERROR 为 0.03。
- L10 技术机制 MATERIAL_ERROR 为 0.04，独立契约 CONTRADICTORY 为 0.05。
- 三章下一步的 TARGETED_REVIEW 分别为 0.08、0.06、0.07。建议均以确定性检查通过为条件。

针对这些分支做了本地逐项核查：

1. **L08 先修与契约**：TOML 表/数组、发行名与导入名、解释器/元数据/实际来源都先解释；普通 int 与输入不变沿用 L01—L05。两个独立目录实际恢复，并验证空、零、2048、负值、bool、浮点和数字文本。stale-lock 例子用排除旧版本的精确要求，不错误声称任何文本改动都必须让锁失效。
2. **L09 raises 与发现**：with 的用法来自 L07，不要求实现协议；新库行为在首次必做独立作业前解释。没有 fixture 参数、装饰器或自定义类。收集不运行、函数未调用的假绿、错误预期和导入阶段错误均真实演示；修复后重新发现执行；三种故意缺陷由原测试捕获而不是改预期。
3. **L10 文件责任与迁移**：TemporaryDirectory 在参考测试前单独解释和实跑。main(path) 是普通可测试参数，不是任意上传路径许可。load 不初始化，app 创建其已知父目录后决定缺失恢复；数据 shape/编码/语法失败保持字节。原子/并发/抗崩溃写入明确排除。预算规划按原顺序贪心跳过，不冒充全局最优算法。
4. **翻译与代码**：简中是主稿，英文完整维护，繁中转换时保护围栏与 inline code。动态展示使用同一规范文件；三语命令/输出围栏逐字一致，中文数据字面量不被翻译改变。

没有发现需要改变已提交英文/下载源码的实质矛盾，因此未为提高概率重复请求。真实请求、响应、元数据与逐文件哈希分章保存。

## 三、确定性验证

### L08

- 16 个白名单条目，6 份 Python，12 份页面共享内容；包含三个独立项目的实际公共 PyPI 锁文件。
- 锁定恢复、解释器/导入来源、业务输出、精确/非精确同步、缺声明修复、遮蔽修复、陈旧锁拒绝、离线冷缓存失败、两个空目录恢复全部实际通过。
- 主项目声明/锁/版本与不兼容父项目文件保持原字节；修复练习只修改副本对应声明和锁，不修改规范材料。

### L09

- 20 个白名单条目，13 份 Python；根套件 6 项、独立预算 9 项真实 pytest 用例通过。
- 普通 assert 的失败、预期错误 1/2/5、故意假绿、发现文件改名修复、错误分支修复、no-dev 下缺 pytest 与恢复均通过。
- 原分支反转、删除 bool 拒绝、独立函数总返回零三种缺陷会让原测试失败，恢复后重新通过。
- 维护层另有 512 个三项任务组合、空和非法输入检查；不把维护测试机制作为学习者先修要求。

### L10

- 20 个白名单条目，13 份 Python，17 份页面共享内容；15 项主需求 pytest 与 2 项独立变式测试通过。
- fresh process 首次/再次、改变 cwd 的实际 --project 命令、35→36、合法空数组、坏 JSON/UTF-8/业务形状拒绝覆盖、临时目录清理、导入无业务目录，以及第二目录恢复均通过。
- 实际反转汇总分支，套件报错；恢复后通过。维护层覆盖 256 个预算规划与 64 个完成/汇总变式。
- 验证不等于生产持久化认证，也未把“只复制一次参考代码”当成读者已掌握；教学仍要求自行实现、解释与迁移。

### 累计与站点

- **131 项 Python unittest、8 项 Node 测试**通过；新增三章的 pytest 另为 **6+9+15+2 项**，不与维护测试数量混写。
- L00—L10 全部实际集成回归通过；保留历史工程的 6 基线、4 刻意练习失败、10 参考用例、陈旧锁拒绝与空目录重建通过。
- 42 篇 js2py MDX、177 个 Python 围栏语法、39 个既有类型声明冒烟片段、三语源码/命令/输出一致性、12 个确定性 ZIP 通过。没有声称所有未重编章节的示例都已执行。
- 全站 678 MDX、TypeScript、ESLint、生产构建通过。保留已有两处 Hook 依赖、Code Hike 空语言、工作区根推断、静态导出 headers/API 和 next lint 弃用提示；没有修改无关框架配置。
- 三章×三语共九个实际页面，在 1280×900 验证标题/侧栏、13/12/13 节、每页三个默认折叠答案并实际点击展开、12/13/17 份源码逐字一致、HTTP ZIP 相等、代码前景色和无整页横向溢出。捕获 18 张截图，实际查看其中 9 张：每章简中顶部、英文展开代码、繁中顶部；不冒称另外九张也已人工查看，不声称覆盖移动端或全站所有交互。

## 四、真实环境故障及恢复

回归最初发现先前临时目录的 CPython 安装缺少运行所需文件，旧历史项目 `.venv` 无法加载 encodings；这不是新业务代码失败。没有禁用测试或修改教材输出去适应损坏环境。

已在本轮专属临时目录重新安装 CPython 3.13.15。核对旧 pyvenv.cfg 指向旧临时路径后，把旧本地环境保留至 `/tmp/langshift-remaining-20260928/legacy-venv-before-rebuild`，再按原锁重建历史环境。未改原锁、未覆盖源码，完整回归随后通过。临时工作区保存初次失败与恢复后的日志。

## 五、未完成范围

这次是完整剩余任务中的一个已验收阶段，不是最终完工。**L11—L14、H01—H06、D01—D06、S01—S03、A01—A02、O01—O06、G01 共 28 章仍未实施**。顺序与授权记录见 `docs/js2py-remaining-execution.zh-cn.md`；状态以章节契约为准，不用空页面、模板或计划文档凑完成数量。
