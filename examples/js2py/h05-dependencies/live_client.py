"""Checks a REAL, already running local API, not an in-process application."""
import argparse
import json
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def check(port: int, summary: bool = False) -> None:
    if not 1 <= port <= 65535:
        raise ValueError("port must be from 1 to 65535")
    base = f"http://127.0.0.1:{port}"

    def send(method: str, path: str, payload=None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(base + path, data=data, method=method,
                          headers={"Content-Type": "application/json"})
        try:
            response = urlopen(request, timeout=5)
        except HTTPError as error:
            response = error  # HTTP rejection still has a status and a response body.
        with response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None

    assert send("GET", "/health") == (200, {"status": "ok"})
    initial = send("GET", "/tasks")[1]
    assert initial["total"] == 0, "Use a fresh server; never run against existing data"
    if summary:
        assert send("GET", "/summary") == (200, {"total": 0, "done": 0, "minutes": 0})
    ids = []
    body_succeeded = False
    try:
        for title, minutes in [("  Read Python  ", 30), ("Write", 0)]:
            status, task = send("POST", "/tasks", {"title": title, "minutes": minutes, "note": "keep"})
            assert status == 201
            ids.append(task["id"])
            assert task == {"id": task["id"], "title": title, "minutes": minutes, "done": False, "note": "keep"}
        first = ids[0]
        assert send("GET", "/tasks?limit=1&offset=1")[1]["items"][0]["id"] == ids[1]
        assert send("PATCH", f"/tasks/{first}", {})[1]["note"] == "keep"
        assert send("PATCH", f"/tasks/{first}", {"note": "changed"})[1]["note"] == "changed"
        assert send("PATCH", f"/tasks/{first}", {"note": None})[1]["note"] is None
        before = send("GET", f"/tasks/{first}")[1]
        assert send("PATCH", f"/tasks/{first}", {"title": "Changed", "minutes": True})[0] == 422
        assert send("GET", f"/tasks/{first}")[1] == before
        for invalid in [True, "3", 3.0, -1]:
            assert send("POST", "/tasks", {"title": "Bad", "minutes": invalid})[0] == 422
        for path in ["/tasks?limit=0", "/tasks?offset=-1", "/tasks/0", "/tasks/no"]:
            assert send("GET", path)[0] == 422
        assert send("GET", "/tasks/99999") == (404, {"detail": "Task not found"})
        if summary:
            assert send("GET", "/summary") == (200, {"total": 2, "done": 0, "minutes": 30})
            assert send("PATCH", f"/tasks/{first}", {"done": True, "minutes": 5})[0] == 200
            assert send("GET", "/summary") == (200, {"total": 2, "done": 1, "minutes": 5})
        print("LIVE PASS: CRUD, strict input, PATCH states, pagination, output allowlist")
        body_succeeded = True
    finally:
        cleanup_errors = []
        for task_id in ids:
            try:
                deleted = send("DELETE", f"/tasks/{task_id}")
                assert deleted == (204, None), f"DELETE expected (204, None), got {deleted!r}"
                missing = send("GET", f"/tasks/{task_id}")
                assert missing[0] == 404, f"GET after DELETE expected 404, got {missing!r}"
            except Exception as error:
                # A failure for one owned ID must not skip the other owned IDs.
                cleanup_errors.append(f"id={task_id}: {type(error).__name__}: {error}")
        if cleanup_errors:
            message = "CLEANUP FAILED (unconfirmed owned IDs): " + "; ".join(cleanup_errors)
            print(message, file=sys.stderr)
            if body_succeeded:
                raise RuntimeError(message)
            # Otherwise the original body exception is already propagating.
            # Do not raise/return here: preserve that traceback AND report cleanup.
    assert send("GET", "/tasks")[1]["total"] == 0
    if summary:
        assert send("GET", "/summary")[1] == {"total": 0, "done": 0, "minutes": 0}
        print("SUMMARY PASS: empty, populated, updated, deleted")
    print("LIVE PASS: cleanup and subsequent 404")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8005)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    check(args.port, args.summary)
