# L02 · Containers, references, and mutation / 容器、引用与修改 / 容器、引用與修改

## 简体中文

前提：完成 L00、L01，能运行脚本，理解基本值、名称绑定、None、方法调用和格式化。本包只使用 CPython 3.13 与内置功能；没有第三方 Python 包、环境配置、循环、函数定义或导入要求。

解压后用编辑器打开 `u02-containers`，让终端位于此目录。每个脚本独立运行，无需加载其他文件的状态：

```sh
uv run --no-project --python 3.13 python lists.py
uv run --no-project --python 3.13 python task_board.py
```

按教材先预测、再运行、再解释，不要把一次运行全部文件当作学完：

| 文件 | 学习问题 |
| --- | --- |
| `lists.py` | 索引、切片、替换、追加、移除和方法返回值各是什么？ |
| `dictionaries.py` | 如何按键组织字段，修改、加入和删除关联？ |
| `missing_values.py` | 缺失、None 和空字符串怎样区分？get 是否写入默认值？ |
| `aliases.py` | 修改共享对象与重新绑定名称有什么不同？ |
| `list_copy.py` | 新外层列表和别名有什么区别？ |
| `shallow_copy.py` | 为什么复制了字典，标签仍然互相影响？ |
| `isolated_copy.py` | 当前数据形状下，怎样隔离将要修改的内层列表？ |
| `repeated_rows.py` | 列表重复为什么可能重复的是同一份内层对象？ |
| `tuples.py` | 元组槽位不可变，为什么内部列表仍然可变？ |
| `sets.py` | 去重、成员与集合运算；为什么排序后打印列表？ |
| `task_board.py` | 哪些对象应该独立，哪些共享是有意的？ |
| `errors/list_index.py` | 故意在第 2 行触发 IndexError，无正常输出 |
| `errors/missing_key.py` | 故意在第 2 行触发 KeyError，无正常输出 |
| `errors/tuple_assignment.py` | 故意在第 2 行触发 TypeError，无正常输出 |
| `errors/unhashable_member.py` | 故意在第 2 行触发 TypeError，无正常输出 |
| `errors/append_rebind.py` | 先打印 None，再在第 4 行触发 TypeError |
| `solutions/fix_draft.py` | 修复草稿标签污染，先自己尝试 |
| `solutions/study_board.py` | 独立综合题参考，先从空文件完成 |

`task_board.py` 应当输出：

```text
Tasks: 2
Read names
['python', 'basics']
['python']
['python']
True
Mina
40
25
```

从空文件独立编写 `study_board.py`。模板为 `{"title": "Untitled", "topics": ["python"], "minutes": 20, "owner": None}`：

1. 派生 `first`、`second` 两份不同的计划字典，模板和两份计划各有独立的主题列表。
2. 第一份标题为 `Read lists`，保留默认时长和负责人字段。
3. 第二份标题为 `Practice dictionaries`，主题新增 `copy`，时长改为 35，删除 owner 字段而不是设为 None。
4. 用列表 `plans` 保存两份计划，按当前字段计算总时长，打印下列结果。

```text
Plans: 2; total: 55 minutes
Read lists
Practice dictionaries
['python']
['python']
['python', 'copy']
True
True
False
False
```

最后四行：第一份存在 owner、它的值是 None、第二份存在 owner、两份主题是同一个对象。用自己的文件验收：

```sh
uv run --no-project --python 3.13 python study_board.py
```

将第二份时长改为 50，总时长应为 70；将模板主题改为 `language`，两份计划应从新模板派生，只有第二份多一个 `copy`。不能硬编码输出，不需要循环、函数、异常捕获或 `import copy`。关系图与完整解释在教材正文。

这些脚本没有网络输入、持久化、数据库或并发控制。针对已知数据形状的复制不是通用深复制，更不是生产后端的数据隔离方案。

## English

Prerequisites: L00 and L01, including local script execution, binding, basic values, None, method calls, and formatting. Use CPython 3.13 and built-ins only. Run the commands above from the extracted `u02-containers` folder, replacing the final filename. Files are independent; there are no third-party packages, project configuration, loops, function definitions, or imports to learn first.

Follow the chapter from lists and dictionaries through missing values, aliasing, shallow copying, nested isolation, repetition, tuples, sets, and the task board. The first four `errors/` files deliberately fail on line 2 without normal output. `errors/append_rebind.py` prints None before a TypeError on line 4. `shallow_copy.py` and `repeated_rows.py` illustrate unintended sharing without raising exceptions. A program that runs is not necessarily correct for its requirement.

Create your own `study_board.py` from the template above. Derive distinct `first` and `second` dictionaries with independently editable topic lists. Keep defaults for the first plan named `Read lists`; name the second `Practice dictionaries`, add topic `copy`, set its duration to 35, and remove its owner field. Put them in `plans`, calculate the total, and produce the specified output. The final four lines check owner presence, None, absence, and topic-list identity.

Vary the second duration to 50 (total 70) and the template topic to `language` (both derive from it; only the second adds `copy`). Do not hard-code results or run the answer as a substitute for independent work. No loops, functions, exception handling, or `import copy` are required. Explanations and relationship diagrams are in the lesson.

These scripts have no public inputs, persistence, database, or concurrency controls. Copying selected levels of a known shape is neither generic deep copying nor a production data-isolation mechanism.

## 繁體中文

前提是完成 L00、L01，能在本地執行腳本，理解名稱綁定、基本值、None、方法呼叫和格式化。本包只用 CPython 3.13 與內建功能。解壓縮後讓終端位於 `u02-containers`，使用上面的命令並替換最後的檔名。每份檔案獨立執行，不需要第三方套件、專案設定、迴圈、函數定義或匯入。

跟著正文逐步學習列表、字典、缺失值、別名、淺複製、巢狀隔離、重複列表、元組、集合與看板。`errors/` 前四個實驗在第 2 行故意失敗而沒有正常輸出；`append_rebind.py` 先輸出 None，再於第 4 行觸發 TypeError。`shallow_copy.py` 和 `repeated_rows.py` 沒有例外，但會展現不符合隔離需求的共享。不要把「能執行」當作業務正確。

用上述模板自行建立 `study_board.py`：產生不同的 `first`、`second` 字典，三份主題列表獨立。第一份標題為 `Read lists` 並保留預設值；第二份為 `Practice dictionaries`，主題新增 `copy`、時長改為 35、刪除 owner 欄位。放入 `plans`，計算總時長並產生指定輸出。最後四行分別檢查負責人欄位存在、值為 None、欄位缺失及兩份主題列表是否為同一物件。

第二份時長改成 50，總時長應為 70；模板主題改成 `language`，兩份計畫都應從新模板衍生，只有第二份多出 `copy`。不要寫死輸出或以執行答案代替獨立練習；不要求迴圈、函數、例外捕獲或 `import copy`。完整機制與關係圖在正文。

腳本沒有網路輸入、持久化、資料庫或並行控制。針對已知資料形狀複製指定層級，並不等於通用深複製或生產後端的資料隔離方案。
