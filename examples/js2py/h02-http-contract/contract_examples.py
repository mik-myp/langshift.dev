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
