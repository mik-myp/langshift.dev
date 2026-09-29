# Task contract h02-task-contract-v2-h04-aligned

2026-09-28. Aligned with H04, still a proposal rather than online H02 CRUD. Use invented data only. See README.md for running and wrapper semantics. Optional hardening gaps below are not core promises; project/identity/database fields require explicit D/S evolution.

## 3. Resources and methods: HTTP semantics are not automatic framework behavior

`/tasks` identifies the collection and `/tasks/1` identifies an item. A resource is neither a local file nor a direct database-table address. H02's static server maps paths to files; later routes dispatch them to business handlers. The same HTTP interface can connect different implementations.

| Method | Meaning and current scope |
| --- | --- |
| GET | Read a collection or item; do not create or delete tasks through a read operation |
| POST | Submit creation to a collection; the service assigns id; repetition may create two items |
| PATCH | Modify explicitly supplied fields; this contract uses absolute assignments, not full replacement |
| DELETE | Remove a task; repeated statuses may differ while the intended effect remains absence |
| HEAD | HTTP defines a GET-like exchange without response content; **not among H04's implemented methods** |
| PUT | Usually replaces the target resource's state; unsupported here, not a PATCH alias |

“Safe” for GET means the caller requests no business-state change. It does not forbid access logs or eliminate security risks. Safe methods, PUT, and DELETE have HTTP-defined idempotent semantics; POST has no general idempotency guarantee. Whether PATCH can be safely repeated depends on the patch's meaning. See [RFC 9110 §9](https://www.rfc-editor.org/rfc/rfc9110.html#section-9) and [RFC 5789](https://www.rfc-editor.org/rfc/rfc5789.html).

The standard defines HEAD, but that does not mean every framework automatically registers HEAD when you declare GET. H01's static tool returns 200 for HEAD, while current H04 returned 405 for HEAD on `/tasks`. This is not permission to ignore HTTP. It is a reason to check “what the protocol means” separately from “what this application supports.”


## 4. Core fields: preservation, strict types, defaults, and output boundaries

This version is `h02-task-contract-v2-h04-aligned`. Complete offline copies are in `CONTRACT.md`, `CONTRACT.zh-cn.md`, and `CONTRACT.zh-tw.md`. The following input/output agreement matches current H04 models without prematurely adding multi-user fields.

| Field | POST creation | PATCH modification | Successful output and constraints |
| --- | --- | --- | --- |
| `title` | Required string | May be omitted; cannot be null when supplied | Original length 1–120; reject all-whitespace text; inspect a stripped copy for validation but **store and return original spelling and surrounding spaces** |
| `minutes` | Required ordinary integer | May be omitted; cannot be null when supplied | At least 0; reject true, numeric strings, and floats rather than coercing them |
| `done` | Optional, default false | May be omitted; cannot be null when supplied | Strict boolean: JSON true/false only, not 0/1 or strings |
| `note` | Optional, default null | Omission preserves; null clears; string replaces | Null or a string of at most 1000 characters; an empty string is valid |
| `id` | Client must not supply it | Client must not supply it | Service-assigned positive integer; no promise of uniqueness across restarts or globally |

String lengths count Python string code points, not UTF-8 bytes or visible graphemes. `"  Ship the draft  "` is valid and retains its spaces; `"   "` is invalid. Changing “not entirely blank” into “trim before saving” changes user data. Frontend and backend cannot independently guess different rules.

POST/PATCH bodies are JSON objects. Unknown fields yield 422, including client-supplied id or internal fields. Successful tasks contain only `id/title/minutes/done/note`. H04 deliberately stores an `internal_tag`, but it must not appear in HTTP output. The output model allowlists public fields instead of exposing the entire storage object.

Strict body types and URL parsing are different concerns. JSON carries number and boolean types; query and path values arrive as text. Strict minutes does not imply an identical literal-validation policy for every query parameter. See [Pydantic strict mode](https://github.com/pydantic/pydantic/blob/v2.12.5/docs/concepts/strict_mode.md) and [FastAPI response models](https://fastapi.tiangolo.com/tutorial/response-model/).


## 5. PATCH is about supplied keys, not merely optional fields

Suppose an existing task's note is `keep me`. Sending only `{"done": true}` modifies completion while preserving note. Sending `{"note": null}` explicitly clears it. `{"note": ""}` is a third meaningful input: store an empty string. A single “remove empty values” operation must not collapse these distinct instructions.

Likewise, minutes 0 and done false are valid explicit changes. Do not use JavaScript's `if (value)` or Python truthiness to decide whether a change applies. Ask **whether the key was supplied**. H04 will use `exclude_unset=True` to extract supplied fields. Establish the semantics first rather than memorizing model APIs.

**An empty PATCH object `{}` is a valid no-change update, returning 200 and the original task.** Model defaults do not mean omitted fields should reset storage. Internal placeholder defaults for minutes/title cannot overwrite existing values; note's default null cannot clear an omitted field. Only note accepts explicit null. Null title/minutes/done yield 422.

Validate all modifications before replacing the learning implementation's in-memory record. A failed PATCH must not leave a changed title alongside rejected minutes. This describes one handler operation, not a guarantee about multiple processes, concurrent read-modify-write, or database transactions. H04's single-process dictionary is a teaching implementation and loses data on restart. Persistence and concurrency boundaries come later. See [FastAPI partial updates](https://fastapi.tiangolo.com/tutorial/body-updates/).


## 6. Requests and responses: explicitly supported interactions

| Request | Normal result | Failures and limitations |
| --- | --- | --- |
| `GET /health` | 200, `{"status":"ok"}` | Only shows that this handler can respond; not task correctness, database readiness, or permission |
| `POST /tasks` | 201, complete public task | Missing fields, wrong types, blank titles, and extra fields yield 422; titles need not be unique |
| `GET /tasks` | 200, `items/limit/offset/total` | Invalid pagination yields 422; an empty collection still succeeds |
| `GET /tasks/{task_id}` | 200, complete public task | id must exceed 0; invalid id yields 422, valid but missing id yields 404 |
| `PATCH /tasks/{task_id}` | 200, complete updated task | Preserve/replace as in section 5; missing task 404, invalid input 422 |
| `DELETE /tasks/{task_id}` | 204, no body | Repetition yields 404; do not parse JSON after successful deletion |

Documented canonical paths have no trailing slash. **H02 does not additionally promise that a trailing slash always returns 404 or never redirects**; framework behavior needs separate checking. Nor do we add an unimplemented JavaScript-safe-integer bound or a prohibition on leading zeros in IDs.

404 for a missing resource is not a connection failure from a stopped service. Unsupported methods generally yield 405 with Allow describing methods reported by the router. The current combination of route declarations does not guarantee that Allow is the complete union of this table. Do not fabricate a header snapshot from the table. Samples preserve observed results, and clients must not treat Allow as authorization.

There is no login, project membership, or task ownership yet. An id is not proof of permission, and guessing a number should not grant access in a future secure system. But **this learning API currently implements no such checks**. Do not call it secure or require an undefined identity field from current clients.


## 7. Errors: keep detail while explaining distinct failure modes

This version follows FastAPI's error shapes: a missing task gives `{"detail":"Task not found"}`; request validation gives `{"detail":[...]}`. A custom `error/code/message/fields` envelope is not described as something the later implementation will automatically provide.

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

The outer `kind/precondition/request/response` is the **teaching wrapper**. The online API sends only response.body. precondition describes the starting tasks assumed by an independent case, not a new network field. Within validation details, `loc` identifies body/query/path and the field, `type` identifies the error category, and `msg` explains it. input/ctx may also appear. Clients can highlight fields by location without relying on an English phrase, array ordering, or every auxiliary key always being present.

| Observation | Interpretation |
| --- | --- |
| 201 + public task | Creation succeeded; keep id; do not assume Location exists |
| 204 + zero body bytes | Deletion succeeded; skip JSON parsing |
| 404 + text detail | No task corresponds to a valid id; not a broken network |
| 422 + detail array | Parameter or body validation failed; correct the request using loc/type |
| Malformed JSON also yields 422 | Current FastAPI uses json_invalid; do not substitute a preferred 400 for actual behavior |
| 405 + text detail | No matching method handler at this path; not an unauthenticated response |
| Unexpected 500 | Server failure, not automatically safe to retry; no promise of the validation error's JSON shape |

HTTP statuses 400, 401, 403, 409, 413, and 415 have useful meanings: request error, identity, permission, business conflict, excessive content, and unsupported media. But **knowing a status does not mean this stage implements its policy**. There is no authentication or uniqueness conflict rule here, so duplicate titles do not magically require 409. See [RFC 9110 §15](https://www.rfc-editor.org/rfc/rfc9110.html#section-15).

Default validation errors can echo input. That is useful with invented teaching data, not a production-redaction guarantee. Do not submit real credentials and then paste the error into logs or tickets. A later uniform envelope or redaction policy requires an explicit version/compatibility plan, not merely edited textbook examples. See [FastAPI error handling](https://fastapi.tiangolo.com/tutorial/handling-errors/).


## 8. Pagination: separate ordering, counts, and the next request

For `GET /tasks`, limit defaults to 20 and ranges from 1 to 100; offset defaults to 0 and must be nonnegative. Order all current tasks by id ascending, then slice. total is the count before slicing, not the current page length. The framework parses query values. We add neither a new strict string grammar nor a promise to automatically reject unknown or duplicate parameters.

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

The first page uses offset=0 and limit=2, returning ids 1 and 2 with total=3. The second uses offset=2 and returns id 3. The response **has no next_offset**. A client can use `offset + items.length < total` to determine whether this observation indicates more data, then request offset+limit. Offset 99 returns 200, empty items, and total=3 rather than 404. Collection existence and item existence are different questions.

There is currently no done/status filter. Adding `done=true` to a URL does not create filtering behavior; current H04 ignores that unknown parameter. To add filtering, revise the contract and then implement parsing, filtering, counting, and tests. Do not let a frontend believe filtering already happened.

Stable ordering only determines order for one dataset, not a snapshot spanning requests. Deleting an earlier task after page one can make the next offset skip an item; concurrent changes can make total stale. We accept this limitation without promising that combined pages represent one instant, or smuggling in database isolation and cursor implementation.

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

preview_page sorts and paginates **already parsed Python values**. check_example checks only its listed sample invariants. Neither is an HTTP parser, complete Pydantic substitute, or CRUD state machine. Passing these checks does not mean a backend has been implemented.


## 9. Idempotency: compare intended effects, not identical statuses

If the first DELETE succeeds but its response is lost, a second DELETE returning 404 does not violate the intended effect that the task is absent. Idempotency concerns the effect of repeated identical requests, not identical bytes or statuses, and does not forbid extra log entries. Current IDs can be reused after process restart, however, so indefinitely retrying an old number is not necessarily operating on the same resource.

POST may create successfully before a response is lost; repeating the same title can create another item. A timeout means the client did not receive a result in time, not that the server did nothing. Disabling a button only reduces mistakes in that UI, not network retries, multiple devices, or reopening a page.

Current PATCH assigns absolute values, such as `{"done": true}`, rather than toggling state. If the same target still exists, no other writer intervenes, and no extra side effect occurs, repeating the assignment leaves the same field state. Not every PATCH is therefore idempotent. Adding increments, notifications, or concurrency versions requires renewed analysis. See [RFC 5789 §2](https://www.rfc-editor.org/rfc/rfc5789.html#section-2).

There is no Idempotency-Key store, transaction, or deduplicated-response cache here. Adding a header cannot grant exactly-once semantics. Do not automatically retry POST. Keep a timed-out write marked “outcome unknown; needs confirmation,” rather than claiming creation definitely failed. S03 will address reliable retries, including key ownership, expiry, changed requests using the same key, and concurrency.


## 10. Optional hardening and present gaps: wishes are not implemented promises

These are actual observations against an isolated copy of current H04 on 2026-09-28, not new core requirements. `gaps/h04-observations.json` records them with source hashes so later changes can be identified.

| Optional policy | Current observation/limit | Work needed if adopted |
| --- | --- | --- |
| Automatically support HEAD | HEAD /tasks returned 405, unlike H01's static tool | Explicit method support and bodyless success/error tests |
| Reject unknown query parameters | `done=true` was ignored; the list remained unfiltered | Parameter model, rejection rules, caller migration |
| Standardize media errors as 415 | text/plain and missing Content-Type experiments both returned 422 | Entry checks, allowed media/charset policy, consistent errors |
| Limit the whole body to 64 KiB with 413 | 70000 spaces plus valid short JSON returned 201 | Byte-based limits before fully reading input; verify proxy and application layers |
| Custom uniform errors without echoed input | Default detail can include input | Exception mapping, redaction, client compatibility, negative tests |

A note-length constraint is not a byte limit on the entire request. A healthy response does not prove these policies exist. Observations apply to the recorded baseline; “no configured limit” is not a promise that a platform accepts infinite input. Give each hardening policy its own requirement and acceptance rather than sending learners after nonexistent H04 promises.

