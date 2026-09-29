# 任務接口契約 h02-task-contract-v2-h04-aligned

2026-09-28。當前階段與H04對齊，仍是提案而非H02在線CRUD。只用虛構數據。運行和包裝語義見README.zh-cn.md。後面的可選加固差距不是當前核心承諾，項目/身份/數據庫字段留給D/S顯式演進。

## 3. 資源與方法：HTTP 語義不等於框架自動實現

`/tasks` 表示任務集合，`/tasks/1` 表示其中一項。資源不是本機文件，也不是數據庫表的直接地址。H02 的靜態服務器恰好把路徑映射到文件，後續路由則把路徑交給業務處理；相同的 HTTP 外形可以連接不同實現。

| 方法 | 語義與當前範圍 |
| --- | --- |
| GET | 讀取集合或單項，不借讀取動作創建或刪除任務 |
| POST | 向集合提交創建要求；由服務分配 id；重複提交可能創建兩項 |
| PATCH | 修改明確提供的字段；本契約使用絕對值設置，不是完整替換 |
| DELETE | 移除指定任務；重複後的狀態可變，目標仍是讓它不存在 |
| HEAD | HTTP 中與 GET 對應但不返回正文；**不在 H04 的已實現方法清單中** |
| PUT | 通常表達目標資源狀態的替換；本版不支持，不能當作 PATCH 的別名 |

GET 的“安全”表示調用者不要求業務狀態改變，不表示不寫訪問日誌或沒有安全風險。安全方法、PUT 和 DELETE 具有 HTTP 規定的冪等語義，POST 沒有通用冪等保證。PATCH 是否可安全重複，需要看具體補丁含義。[RFC 9110 §9](https://www.rfc-editor.org/rfc/rfc9110.html#section-9)、[RFC 5789](https://www.rfc-editor.org/rfc/rfc5789.html)

標準定義 HEAD 的語義，不代表每個框架的 GET 聲明都會自動註冊 HEAD。H01 靜態工具對 HEAD 返回 200，而當前 H04 對 `/tasks` 的 HEAD 實測 405；這不是讓你忽略協議，而是提醒你分別核對“協議如何定義”和“應用實際支持什麼”。


## 4. 核心字段：原樣、嚴格類型、默認值與輸出邊界

本版名為 `h02-task-contract-v2-h04-aligned`。離線完整約定在 `CONTRACT.md`、`CONTRACT.zh-cn.md`、`CONTRACT.zh-tw.md`。下面是與當前 H04 模型一致的輸入與輸出，不把未來多用戶字段提前放入當前 API。

| 字段 | POST 創建 | PATCH 修改 | 成功響應與約束 |
| --- | --- | --- | --- |
| `title` | 必填字符串 | 可省略；提供時不能為 null | 原字符串長度 1–120；全部空白拒絕；驗證時檢查去空白副本，**保存和返回原字形及首尾空白** |
| `minutes` | 必填普通整數 | 可省略；提供時不能為 null | 大於等於 0；拒絕 true、字符串數字和浮點數，不自動強制轉換 |
| `done` | 可省略，默認 false | 可省略；提供時不能為 null | 嚴格布爾值，只接受 JSON true/false，不接受 0/1 或字符串 |
| `note` | 可省略，默認 null | 省略保留；null 清除；字符串替換 | null 或最長 1000 字符的字符串；空字符串也是合法值 |
| `id` | 禁止客戶端提供 | 禁止客戶端提供 | 服務分配的正整數；不承諾跨重啟唯一或全局唯一 |

字符串長度按 Python 字符串的碼點計數，不按 UTF-8 字節或可見字形。`"  Ship the draft  "` 合法且空白保留；`"   "` 不合法。把“不能全空白”偷換成“保存時 trim”會改變用戶數據，前後端不能各自猜一種規則。

POST/PATCH 正文是 JSON 對象，未知字段拒絕為 422，包括自報 id 或內部字段。成功任務只有 `id/title/minutes/done/note`；H04 故意在存儲中加入 `internal_tag`，但它不應出現在 HTTP 輸出。輸出模型是公開字段白名單，不是把整個存儲對象直接透傳。

正文的嚴格類型與 URL 參數的解析不是一回事：JSON 自帶數字、布爾值等類型，查詢和路徑則先以文本到達。不要從“minutes 嚴格整數”推出“所有 query 參數必須按相同字面形式校驗”。[Pydantic strict mode](https://github.com/pydantic/pydantic/blob/v2.12.5/docs/concepts/strict_mode.md)、[FastAPI 響應模型](https://fastapi.tiangolo.com/tutorial/response-model/)


## 5. PATCH 的關鍵不是“可選”，而是有沒有提供這個鍵

假設已有任務 note 為 `keep me`。只提交 `{"done": true}`，表示只修改完成狀態，note 必須保留；提交 `{"note": null}` 才明確清除。`{"note": ""}` 又是第三種有意義的輸入：保存空字符串。它們不能全部被一次“過濾空值”合併成相同操作。

同理，minutes 為 0 和 done 為 false 都是有效的顯式修改，不能用 JS 的 `if (value)` 或 Python 的真假判斷來決定是否應用。判斷的是**鍵是否出現**。H04 將以 `exclude_unset=True` 提取已提供字段；這裡先建立語義，不先要求背模型 API。

**空 PATCH 對象 `{}` 是合法的無變化更新，返回 200 與原任務。** 默認值服務於模型構造，不意味著省略字段就要重置存儲。minutes/title 的內部佔位默認值不能覆蓋已有值，note 的默認 null 也不能清除省略字段。只有 note 接受顯式 null；title/minutes/done 的 null 為 422。

所有修改先驗證，再整體替換學習版內存記錄；一次失敗 PATCH 不應留下標題已改、minutes 未改的半成品。這是單次處理的約定，不是對多進程、併發讀改寫或數據庫事務的保證。H04 的單進程字典只是學習實現，重啟會丟數據，後面才建立持久化與併發邊界。[FastAPI 部分更新](https://fastapi.tiangolo.com/tutorial/body-updates/)


## 6. 從請求到響應：當前明確支持的交互

| 請求 | 正常結果 | 失敗與邊界 |
| --- | --- | --- |
| `GET /health` | 200，`{"status":"ok"}` | 僅表明該處理路徑能響應，不證明任務正確、數據庫可用或有權限 |
| `POST /tasks` | 201，完整公開任務 | 缺字段、非法類型、空白標題、額外字段為 422；沒有標題唯一約束 |
| `GET /tasks` | 200，`items/limit/offset/total` | 分頁參數不合要求為 422；空集合仍是成功 |
| `GET /tasks/{task_id}` | 200，完整公開任務 | id 要大於 0；非法 id 為 422，合法但不存在為 404 |
| `PATCH /tasks/{task_id}` | 200，完整修改後任務 | 按第 5 節保留/替換；不存在為 404，非法輸入為 422 |
| `DELETE /tasks/{task_id}` | 204，沒有正文 | 再次刪除為 404；客戶端不解析成功響應的 JSON |

提供給讀者的規範路徑沒有結尾斜槓。**不在 H02 額外承諾尾斜槓一定 404 或一定無重定向**；框架行為必須另測。也不為 ID 增加 H04 未實施的 JavaScript 安全整數上限或“禁止前導零”等新規則。

無此資源得到 404，不能與“服務沒啟動”的連接失敗混淆；不支持的方法通常得到 405，響應帶 Allow 表示路由器報告的允許方法。當前路由聲明的組合不保證 Allow 是整張表的完整並集，不能根據自己寫的表偽造一條頭部快照。樣本保留實際核對結果，客戶端不要把這個頭當授權許可。

此時沒有登錄、項目成員或任務所有權。id 不是權限證明，能猜到編號不應在未來自動取得訪問權，但**當前學習版根本沒有實施那層檢查**。所以既不把樣本稱為安全 API，也不要求當前客戶端發送尚未定義的身份字段。


## 7. 錯誤：沿用 detail，仍要解釋清楚每種失敗

本版沿用 FastAPI 的錯誤形態：不存在任務是 `{"detail":"Task not found"}`；請求驗證失敗是 `{"detail":[...]}`。不把自創的 `error/code/message/fields` 信封描述為後續默認會實現的行為。

```json
{
  "kind": "proposed-contract-example",
  "name": "blank-title",
  "precondition": {
    "seed_tasks": []
  },
  "request": {
    "method": "POST",
    "target": "/tasks",
    "headers": {
      "Content-Type": "application/json"
    },
    "body": {
      "title": "   ",
      "minutes": 15
    }
  },
  "response": {
    "status": 422,
    "headers": {
      "Content-Type": "application/json"
    },
    "body": {
      "detail": [
        {
          "type": "value_error",
          "loc": [
            "body",
            "title"
          ],
          "msg": "Value error, title must not be blank",
          "input": "   ",
          "ctx": {
            "error": {}
          }
        }
      ]
    }
  }
}
```

外層 `kind/precondition/request/response` 是**教學樣本包裝**；在線 API 只發送其中 response.body。precondition 記錄這個獨立案例假定的初始任務，不是新增網絡字段。驗證項裡 `loc` 定位 body/query/path 和字段，`type` 描述錯誤種類，`msg` 是解釋文本；有時還包含 input/ctx。客戶端可據位置標出字段錯誤，不應依賴英文句子的某個詞、數組順序或所有輔助鍵始終存在。

| 觀察 | 應如何理解 |
| --- | --- |
| 201 + 公開任務 | 創建成功，保存返回的 id；不假定有 Location |
| 204 + 零字節正文 | 刪除成功，跳過 JSON 解析 |
| 404 + 文本 detail | 合法編號對應的任務不存在；不是網絡斷線 |
| 422 + detail 數組 | 參數或正文驗證失敗；根據 loc/type 修正請求 |
| 畸形 JSON 也為 422 | 當前 FastAPI 使用 json_invalid；不要把自己偏好的 400 寫成當前事實 |
| 405 + 文本 detail | 此路徑沒有對應方法處理器；不等於未認證 |
| 未預期的 500 | 服務端故障，不應自動當成安全重試信號；也不承諾它使用驗證錯誤的 JSON 格式 |

HTTP 中 400、401、403、409、413、415 都有各自用途：請求錯誤、身份、權限、業務衝突、過大正文和不支持的媒體類型。但**知道狀態碼的含義，不等於本階段已實現對應政策**。例如當前無身份驗證，也無衝突唯一性規則，不能憑空要求重複標題變成 409。[RFC 9110 §15](https://www.rfc-editor.org/rfc/rfc9110.html#section-15)

默認驗證錯誤可能回顯輸入。它適合觀察虛構實驗數據，但不是生產脫敏保證；不要提交真實憑證，再把錯誤貼進日誌或工單。後續若統一錯誤信封或脫敏，需要明確版本變化和兼容策略，而不是隻在教材裡改示例。[FastAPI 錯誤處理](https://fastapi.tiangolo.com/tutorial/handling-errors/)


## 8. 分頁：把排序、總數和下一次請求拆開

`GET /tasks` 的 limit 默認 20、範圍 1–100；offset 默認 0、必須大於等於 0。服務按 id 升序排列全部當前任務，再切片；total 是切片前總數，不是當前頁長度。查詢參數由框架解析，本章不新增一套嚴格字符串語法，也不承諾未知或重複 query 自動拒絕。

```json
{
  "kind": "proposed-contract-example",
  "name": "list-first",
  "precondition": {
    "seed_tasks": [
      {
        "title": "  Read HTTP  ",
        "minutes": 25,
        "done": false,
        "note": "keep me"
      },
      {
        "title": "Check the failure path",
        "minutes": 0,
        "done": true,
        "note": null
      },
      {
        "title": "Write an independent case",
        "minutes": 40,
        "done": false,
        "note": "later"
      }
    ]
  },
  "request": {
    "method": "GET",
    "target": "/tasks?offset=0&limit=2",
    "headers": {}
  },
  "response": {
    "status": 200,
    "headers": {
      "Content-Type": "application/json"
    },
    "body": {
      "items": [
        {
          "id": 1,
          "title": "  Read HTTP  ",
          "minutes": 25,
          "done": false,
          "note": "keep me"
        },
        {
          "id": 2,
          "title": "Check the failure path",
          "minutes": 0,
          "done": true,
          "note": null
        }
      ],
      "limit": 2,
      "offset": 0,
      "total": 3
    }
  }
}
```

```json
{
  "kind": "proposed-contract-example",
  "name": "list-last",
  "precondition": {
    "seed_tasks": [
      {
        "title": "  Read HTTP  ",
        "minutes": 25,
        "done": false,
        "note": "keep me"
      },
      {
        "title": "Check the failure path",
        "minutes": 0,
        "done": true,
        "note": null
      },
      {
        "title": "Write an independent case",
        "minutes": 40,
        "done": false,
        "note": "later"
      }
    ]
  },
  "request": {
    "method": "GET",
    "target": "/tasks?offset=2&limit=2",
    "headers": {}
  },
  "response": {
    "status": 200,
    "headers": {
      "Content-Type": "application/json"
    },
    "body": {
      "items": [
        {
          "id": 3,
          "title": "Write an independent case",
          "minutes": 40,
          "done": false,
          "note": "later"
        }
      ],
      "limit": 2,
      "offset": 2,
      "total": 3
    }
  }
}
```

第一頁 offset=0、limit=2，得到 id 1、2，total=3；第二頁 offset=2，得到 id 3。響應**沒有 next_offset**。客戶端根據 `offset + items.length < total` 判斷這次觀察是否還有後續數據，下一次可請求 offset+limit。offset=99 則得到 200、空 items、total=3，不是 404：集合存在與單項存在是兩件事。

當前沒有 done/status 篩選接口。給 URL 加 `done=true` 不會自動產生過濾功能；在當前 H04 中這類未知 query 被忽略。需要篩選時應先修訂契約，再加解析、過濾、計數與測試，不能讓前端以為已經篩過。

穩定排序只解決同一數據集的順序，不提供跨請求快照。第一頁後有人刪除較前面的任務，下一頁的 offset 可能跳過一項；併發變化也可能令 total 過時。當前接受這個限制，不承諾每頁組合就是某個時刻的完整快照，更不偷渡數據庫隔離或遊標實現。

```python
"""H04-aligned proposed samples, NOT a CRUD backend or request validator."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASE_NAMES = (
    "list-first", "list-last", "list-empty", "list-default", "get-task",
    "create-ok", "patch-title", "patch-clear-note", "delete-ok", "delete-again",
    "missing-task", "blank-title", "bad-page", "bool-minutes", "wrong-method",
    "malformed-json", "null-title", "server-field", "missing-minutes",
    "string-minutes", "nonbool-done", "empty-patch", "patch-zero-false",
    "patch-omit-note",
)
PUBLIC_FIELDS = {"id", "title", "minutes", "done", "note"}


def read_case(name: str) -> dict:
    if name not in CASE_NAMES:
        raise ValueError("unknown contract example")
    return json.loads((ROOT / "public" / "exchanges" / f"{name}.json").read_text(encoding="utf-8"))


def check_task_example(task: dict) -> None:
    """Selected output invariants, not a substitute for H04's Pydantic models."""
    if set(task) != PUBLIC_FIELDS:
        raise ValueError("public task fields must match the core contract")
    if type(task["id"]) is not int or task["id"] <= 0:
        raise ValueError("id must be a positive integer")
    if not isinstance(task["title"], str) or not 1 <= len(task["title"]) <= 120 or not task["title"].strip():
        raise ValueError("title must be a nonblank string of 1..120 characters")
    if type(task["minutes"]) is not int or task["minutes"] < 0:
        raise ValueError("minutes must be a nonnegative integer, not bool")
    if type(task["done"]) is not bool:
        raise ValueError("done must be bool")
    if task["note"] is not None and (not isinstance(task["note"], str) or len(task["note"]) > 1000):
        raise ValueError("note must be null or a string of at most 1000 characters")


def check_example(example: dict) -> None:
    """Check selected sample consistency, not arbitrary HTTP input or state."""
    if example["kind"] != "proposed-contract-example":
        raise ValueError("example must be marked as proposed")
    response = example["response"]
    status, headers, body = response["status"], response["headers"], response["body"]
    if status == 204:
        if body is not None or "Content-Type" in headers:
            raise ValueError("204 must not promise a JSON body")
        return
    if headers.get("Content-Type") != "application/json":
        raise ValueError("these core examples use JSON except for 204")
    if status >= 400:
        if set(body) != {"detail"}:
            raise ValueError("core errors use detail, not a custom error envelope")
        if status == 422:
            if not isinstance(body["detail"], list) or not body["detail"]:
                raise ValueError("422 needs a nonempty validation detail list")
            for issue in body["detail"]:
                if not {"loc", "type", "msg"} <= set(issue):
                    raise ValueError("validation details need loc/type/msg")
        elif not isinstance(body["detail"], str):
            raise ValueError("404/405 examples use a text detail")
        return
    if isinstance(body, dict) and "items" in body:
        if set(body) != {"items", "limit", "offset", "total"}:
            raise ValueError("page must not invent next_offset or filtering metadata")
        if not 1 <= body["limit"] <= 100 or body["offset"] < 0 or body["total"] < len(body["items"]):
            raise ValueError("invalid page metadata")
        if len(body["items"]) > body["limit"]:
            raise ValueError("page exceeds limit")
        for task in body["items"]:
            check_task_example(task)
    else:
        check_task_example(body)
    if status == 201 and body["title"] != example["request"]["body"]["title"]:
        raise ValueError("creation preserves original title spelling and spaces")


def preview_page(tasks: list[dict], offset=0, limit=20) -> dict:
    """Pure preview of parsed values. Not a query parser, filter, or database."""
    if type(offset) is not int or offset < 0:
        raise ValueError("offset must be a nonnegative integer")
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    ordered = sorted(tasks, key=lambda task: task["id"])
    return {"items": ordered[offset:offset + limit], "limit": limit,
            "offset": offset, "total": len(ordered)}


if __name__ == "__main__":
    for name in CASE_NAMES:
        example = read_case(name)
        check_example(example)
        request = example["request"]
        print(f"PROPOSED {request['method']} {request['target']} -> {example['response']['status']}")
    print(f"checked {len(CASE_NAMES)} proposed exchanges; no CRUD requests executed")
```

preview_page 只計算**已解析 Python 值**的排序與分頁，check_example 只驗證列出的樣本不變量。二者不是 HTTP 解析器、完整 Pydantic 替身或 CRUD 狀態機；通過這些檢查不代表後端已經實現。


## 9. 冪等：比較預期效果，而非每次狀態相同

第一次 DELETE 成功而響應丟失，再次 DELETE 得到 404，並不破壞“該任務不存在”的效果。冪等關注同樣請求重複後的預期業務效果，不要求響應字節或狀態完全一樣，也不禁止多一條訪問日誌。當前 id 可能在進程重啟後重用，因此不能無限期重試舊編號，再聲稱仍在操作同一資源。

POST 則可能第一次已創建、只是響應沒到達；重複發送同一標題會創建第二項。超時說明客戶端沒有及時拿到結果，不證明服務端沒做事。禁用提交按鈕只減少這份 UI 中的誤點，不能覆蓋網絡重試、多設備或重新打開頁面。

當前 PATCH 設置絕對值，例如 `{"done": true}`，不是“切換狀態”。在同一目標仍存在、無其他寫入、無額外副作用的條件下，重複相同設置得到相同字段狀態；這不意味著所有 PATCH 都冪等。以後加入累加、通知或併發版本檢查，必須重新分析業務效果。[RFC 5789 §2](https://www.rfc-editor.org/rfc/rfc5789.html#section-2)

本章沒有 Idempotency-Key 存儲、事務或去重響應緩存。多傳一個頭部不會自動獲得恰好一次語義。現在不自動重試 POST；寫操作超時時先保留“結果未知、待確認”，不要把它錯誤顯示成確定的創建失敗。可靠重試留到 S03，必須說明鍵歸屬、有效期、同鍵不同請求與併發處理。


## 10. 可選加固與當前差距：不能把願望寫成已實現契約

以下是 2026-09-28 對當前 H04 隔離副本的實際觀察，不是新增主線要求。完整記錄在 `gaps/h04-observations.json`，帶源碼摘要，便於以後判斷實現是否變化。

| 可選政策 | 當前觀察／邊界 | 若以後採用，必須補什麼 |
| --- | --- | --- |
| 自動支持 HEAD | HEAD /tasks 為 405；H01 靜態工具卻支持 | 顯式方法支持、無正文與錯誤路徑測試 |
| 拒絕未知 query | `done=true` 被忽略，仍返回未過濾列表 | 參數模型、拒絕規則、調用方遷移 |
| 統一媒體類型錯誤為 415 | text/plain 和缺 Content-Type 的實驗均為 422 | 入口檢查、允許媒體類型/charset 和一致錯誤策略 |
| 限制整段正文到 64 KiB 並返回 413 | 70000 個空格加合法短 JSON 的 POST 為 201 | 明確按字節限額，在完整讀取前限制，並驗證代理/應用兩層 |
| 統一自定義錯誤、禁止輸入回顯 | 默認 detail 可能攜帶 input | 異常映射、脫敏、客戶端兼容與負向測試 |

字段 note 長度上限不等於整個請求體的字節限制；有健康響應也不等於具備這些政策。當前觀察只適用於記錄的基線，不能把“沒配置限額”解讀成平臺保證無限接收。可選加固都應有獨立需求與驗收，不偷偷讓初學者在 H04 必測用例中追一個不存在的承諾。

