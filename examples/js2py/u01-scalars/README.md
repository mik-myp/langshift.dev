# L01 · Names, values, and basic operations / 名称、值与基本运算 / 名稱、值與基本運算

## 简体中文

前提是已经完成 L00，能创建并运行一份 Python 脚本。本包只使用 CPython 3.13 和内置功能；没有要安装的第三方包、项目配置、测试工具或服务。每个脚本独立运行，无须按顺序加载状态。

解压后，在编辑器中打开 `u01-scalars`，让终端位于这个文件夹。沿用 L00 的命令：

```sh
uv run --no-project --python 3.13 python bindings.py
uv run --no-project --python 3.13 python task_estimate.py
```

第二个命令的预期输出：

```text
Task: Read Python basics
Estimate: 1h 35m
Decimal hours: 1.58
```

建议按教材顺序逐段阅读、先预测再运行，不要一次运行所有文件：

| 文件 | 问题 |
| --- | --- |
| `bindings.py` | 重新绑定为什么不改变另一个名称或旧输出？ |
| `scalar_types.py` | `30`、`30.0`、`"30"`、布尔值、None 怎样区分？ |
| `numbers.py` | `/`、`//`、`%`、负数和结果类型怎样工作？ |
| `boolean_none.py` | 值相等与 None 检查各在问什么？ |
| `strings.py` | 清理文本为何不修改原始字符串？ |
| `conversions.py` | 转换结果与原始输入有什么区别？ |
| `formatting.py` | 文字快照与显示精度怎样工作？ |
| `task_estimate.py` | 怎样串联输入、转换、计算与显示？ |
| `errors/text_plus_number.py` | 故意产生 TypeError，没有正常输出 |
| `errors/invalid_integer.py` | 故意产生 ValueError，没有正常输出 |
| `solutions/fix_minutes.py` | 排错题的独立参考，先自己修复 |
| `solutions/reading_plan.py` | 综合题的独立参考，先从空文件完成 |

综合练习：自己创建 `reading_plan.py`，从 `raw_topic = "  Python names  "`、`raw_sessions = "4"`、`minutes_per_session = 25` 出发，清理主题，转换次数，计算总分钟、小时和余数。应当输出：

```text
Topic: Python names
Sessions: 4
Total: 100 minutes (1h 40m)
```

运行自己写的文件：

```sh
uv run --no-project --python 3.13 python reading_plan.py
```

将次数改成 `"5"`，应得到 `125 minutes (2h 5m)`。不要只运行参考答案，也不要硬编码输出。故意改成 `"many"` 时，应能解释转换行的 ValueError；无需异常捕获。完整动机、机制、错误解释和分级练习在对应三语教材页面中。

这些输入由作者写在源码里，不是用户请求。转换成功不等于完成输入校验；本包不检查负时长、空标题等业务规则，不是可直接上线的后端。

## English

Prerequisite: finish L00 and be able to create and run a Python script. These independent files use CPython 3.13 and built-ins only. No third-party packages, project configuration, tests, or services are required. Run the commands above from the extracted `u01-scalars` folder, replacing the final filename for each experiment.

Follow the chapter: bindings → types → arithmetic → comparisons/None → strings → conversion → formatting → task estimate. Predict before running. The two `errors/` programs deliberately stop with TypeError and ValueError respectively, without normal output. This is expected, not a broken download. The `solutions/` files are separate references to read after an independent attempt.

Create your own `reading_plan.py` from the three input values shown above. Clean the topic, convert the count, calculate the duration, and produce the three specified lines. Changing the count to `"5"` must produce `125 minutes (2h 5m)` without changing calculation code. Diagnose the ValueError when the count becomes `"many"`; exception handling is not required. The chapter contains the complete explanations and graduated exercises.

Inputs are trusted source literals, not public requests. Successful conversion is not complete validation. Negative durations and empty titles are not checked. This is a language exercise, not a production backend.

## 繁體中文

前提是已完成 L00，能自行建立並執行 Python 腳本。本包只用 CPython 3.13 與內建功能，不需要第三方套件、專案設定、測試工具或服務。每份檔案獨立執行；解壓縮後，讓終端位於 `u01-scalars`，使用上面的命令並替換最後的檔名。

跟著教材依序學習：名稱綁定 → 型別 → 運算 → 比較與 None → 字串 → 轉換 → 格式化 → 任務估時。先預測，再執行。`errors/` 內兩個程式故意產生 TypeError 與 ValueError，沒有正常輸出，這不是下載損壞。`solutions/` 是獨立嘗試後才看的參考。

使用上述三個輸入，自行建立 `reading_plan.py`：清理主題、轉換次數、計算時長，產生指定的三行輸出。次數改為 `"5"` 時，應得到 `125 minutes (2h 5m)`，不修改計算程式碼。輸入 `"many"` 時能定位並解釋 ValueError 即可，不要求例外捕獲。完整解釋與分級練習在教材正文。

輸入是寫在原始碼內的可信值，不是公眾請求。轉換成功不代表完整驗證；負時長與空標題等業務規則尚未檢查。這是語言練習，不是可直接上線的後端。
