"""Maintainer real-socket verification of H03/H04; never a learner prerequisite.

Only owned loopback processes are started/stopped. Logs use a fresh private
temporary directory. JS2PY_LAB_ROOT may select an extracted download tree.
"""

import json
import os
import re
import signal
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(
    os.environ.get(
        "JS2PY_LAB_ROOT", str(Path(__file__).resolve().parents[1] / "examples/js2py")
    )
).resolve()
OUT = Path(tempfile.mkdtemp(prefix="js2py-fastapi-check-"))
ENV = dict(
    os.environ,
    PATH=str(Path.home() / ".local/bin") + os.pathsep + os.environ.get("PATH", ""),
)
for key in [
    "PYTHONPATH",
    "PYTHONHOME",
    "VIRTUAL_ENV",
    "UV_PROJECT_ENVIRONMENT",
    "UV_ACTIVE",
    "UV_PYTHON",
]:
    ENV.pop(key, None)
ENV["PYTHONIOENCODING"] = "utf-8"
cases = []
procs = []


def record(lab, name, **kw):
    cases.append(dict(lab=lab, case=name, **kw))
    print(lab, name, kw.get("status", kw.get("returncode", "PASS")), flush=True)


def request(port, method, path, body=None, raw=None):
    data = (
        raw
        if raw is not None
        else (json.dumps(body).encode() if body is not None else None)
    )
    req = Request(
        f"http://127.0.0.1:{port}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data is not None else {},
    )
    try:
        with urlopen(req, timeout=5) as r:
            return r.status, r.read(), dict(r.headers)
    except HTTPError as r:
        return r.code, r.read(), dict(r.headers)


def check(lab, name, port, method, path, expected, body=None, predicate=None, raw=None):
    status, content, headers = request(port, method, path, body, raw)
    try:
        result = json.loads(content)
    except (ValueError, TypeError):
        result = content.decode()
    assert status == expected, (name, status, result)
    if predicate:
        assert predicate(result), (name, result)
    record(
        lab,
        name,
        method=method,
        path=path,
        input=body if raw is None else raw.decode(),
        status=status,
        body=result,
        body_bytes=len(content),
        content_type=headers.get("content-type"),
    )
    return result


def start(lab, target="app:app", health="/health", from_parent=False):
    port = 0
    logpath = OUT / f"{lab}-{target.replace(':', '-').replace('.', '-')}-{port}.log"
    f = logpath.open("w")
    cmd = [
        "uv",
        "run",
        "--locked",
        "python",
        "-m",
        "uvicorn",
        target,
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--workers",
        "1",
    ]
    if from_parent:
        cmd[1:1] = ["--project", str(ROOT / lab)]
        cmd += ["--app-dir", str(ROOT / lab)]
    p = subprocess.Popen(
        cmd,
        cwd=ROOT if from_parent else ROOT / lab,
        env=ENV,
        stdout=f,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    procs.append((p, f, logpath))
    for _ in range(100):
        if p.poll() is not None:
            raise RuntimeError(logpath.read_text())
        match = re.search(
            r"Uvicorn running on http://127\.0\.0\.1:(\d+)", logpath.read_text()
        )
        if match:
            port = int(match.group(1))
            try:
                request(port, "GET", health)
                break
            except (URLError, ConnectionError, TimeoutError):
                pass
        time.sleep(0.05)
    else:
        raise RuntimeError("startup timeout")
    record(
        lab,
        "start " + target,
        command=cmd,
        cwd=str(ROOT if from_parent else ROOT / lab),
        pid=p.pid,
        port=port,
        log=str(logpath),
    )
    return p, port, logpath


def stop(p):
    if p.poll() is None:
        os.killpg(p.pid, signal.SIGINT)
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait(timeout=5)


def command(lab, name, args, cwd=None, expected=1, contains=None):
    result = subprocess.run(
        args, cwd=cwd or ROOT / lab, env=ENV, capture_output=True, text=True, timeout=20
    )
    assert result.returncode == expected, (
        name,
        result.returncode,
        result.stdout,
        result.stderr,
    )
    text = result.stdout + result.stderr
    if contains:
        assert contains in text, (name, text)
    record(
        lab,
        name,
        command=args,
        cwd=str(cwd or ROOT / lab),
        returncode=result.returncode,
        output=text,
    )


try:
    lab = "h03-first-fastapi"
    p, port, log = start(lab)
    check(
        lab,
        "health",
        port,
        "GET",
        "/health",
        200,
        predicate=lambda x: x == {"status": "ok"},
    )
    check(
        lab,
        "read seed",
        port,
        "GET",
        "/tasks/1",
        200,
        predicate=lambda x: (
            x
            == {
                "id": 1,
                "title": "Read HTTP",
                "minutes": 25,
                "done": False,
                "note": None,
            }
        ),
    )
    check(
        lab,
        "list",
        port,
        "GET",
        "/tasks",
        200,
        predicate=lambda x: x["total"] == 2 and len(x["items"]) == 2,
    )
    check(
        lab,
        "page",
        port,
        "GET",
        "/tasks?limit=1&offset=1",
        200,
        predicate=lambda x: x["items"][0]["id"] == 2 and x["total"] == 2,
    )
    check(
        lab,
        "empty page",
        port,
        "GET",
        "/tasks?offset=99",
        200,
        predicate=lambda x: x["items"] == [] and x["total"] == 2,
    )
    for name, path, status in [
        ("missing id", "/tasks/999", 404),
        ("text id", "/tasks/nope", 422),
        ("zero id", "/tasks/0", 422),
        ("negative id", "/tasks/-1", 422),
        ("zero limit", "/tasks?limit=0", 422),
        ("large limit", "/tasks?limit=101", 422),
        ("text limit", "/tasks?limit=nope", 422),
        ("negative offset", "/tasks?offset=-1", 422),
        ("unknown route", "/missing", 404),
    ]:
        check(lab, name, port, "GET", path, status)
    check(lab, "wrong method", port, "POST", "/tasks", 405)
    check(
        lab,
        "OpenAPI",
        port,
        "GET",
        "/openapi.json",
        200,
        predicate=lambda x: "/tasks/{task_id}" in x["paths"],
    )
    command(
        lab,
        "port collision",
        [
            "uv",
            "run",
            "--locked",
            "python",
            "-m",
            "uvicorn",
            "app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--workers",
            "1",
        ],
        contains="address already in use",
    )
    check(lab, "original survives collision", port, "GET", "/health", 200)
    command(
        lab,
        "wrong working directory",
        [
            "uv",
            "run",
            "--project",
            str(ROOT / lab),
            "--locked",
            "python",
            "-m",
            "uvicorn",
            "app:app",
            "--host",
            "127.0.0.1",
            "--port",
            "0",
        ],
        cwd=ROOT,
        contains='Could not import module "app"',
    )
    command(
        lab,
        "missing attribute",
        [
            "uv",
            "run",
            "--locked",
            "python",
            "-m",
            "uvicorn",
            "app:missing",
            "--host",
            "127.0.0.1",
            "--port",
            "0",
        ],
        contains='Attribute "missing" not found',
    )
    command(
        lab,
        "import diagnostic",
        [
            "uv",
            "run",
            "--locked",
            "python",
            "-c",
            "import app; print(type(app.app).__name__)",
        ],
        expected=0,
        contains="FastAPI",
    )
    command(
        lab,
        "python file is not server",
        ["uv", "run", "--locked", "python", "app.py"],
        expected=0,
    )
    stop(p)
    try:
        request(port, "GET", "/health")
        raise AssertionError("still listening")
    except URLError as e:
        record(
            lab, "connection refused after stop", error=str(e), returncode=p.returncode
        )
    p, port, log = start(lab, "errors.broken_app:app", health="/broken")
    check(
        lab,
        "unhandled application bug",
        port,
        "GET",
        "/broken",
        500,
        predicate=lambda x: x == "Internal Server Error",
    )
    stop(p)
    assert "RuntimeError: deliberate failure for H03" in log.read_text()
    record(
        lab,
        "traceback stays in log",
        log=str(log),
        contains="RuntimeError: deliberate failure for H03",
    )
    p, port, log = start(lab)
    check(lab, "normal health recovery after 500", port, "GET", "/health", 200)
    check(lab, "normal task recovery after 500", port, "GET", "/tasks/1", 200)
    stop(p)
    p, port, log = start(lab, from_parent=True)
    check(lab, "app-dir recovery from parent", port, "GET", "/health", 200)
    stop(p)
    p, port, log = start(lab, "solutions.rebuild:app")
    check(
        lab,
        "independent summary",
        port,
        "GET",
        "/summary",
        200,
        predicate=lambda x: x == {"count": 1, "minutes": 25},
    )
    check(
        lab,
        "independent rebuild page",
        port,
        "GET",
        "/tasks?limit=1&offset=1",
        200,
        predicate=lambda x: x["items"][0]["id"] == 2,
    )
    stop(p)
    lab = "h04-validation"
    command(
        lab,
        "runtime model probe",
        ["uv", "run", "--locked", "python", "probe_models.py"],
        expected=0,
        contains="nullable but missing: missing",
    )
    command(
        lab,
        "patch probe",
        ["uv", "run", "--locked", "python", "probe_patch.py"],
        expected=0,
        contains="WRONG exclude_none: {}",
    )
    p, port, log = start(lab)
    keys = {"id", "title", "minutes", "done", "note"}

    def public(value):
        return set(value) == keys

    check(
        lab,
        "empty list",
        port,
        "GET",
        "/tasks",
        200,
        predicate=lambda x: x == {"items": [], "limit": 20, "offset": 0, "total": 0},
    )
    first = check(
        lab,
        "create with spelling preserved",
        port,
        "POST",
        "/tasks",
        201,
        {"title": "  Read HTTP  ", "minutes": 25, "note": "keep me"},
        lambda x: (
            public(x)
            and x["id"] == 1
            and x["title"] == "  Read HTTP  "
            and x["done"] is False
        ),
    )
    check(
        lab,
        "create zero and defaults",
        port,
        "POST",
        "/tasks",
        201,
        {"title": "Zero", "minutes": 0},
        lambda x: (
            public(x)
            and x["id"] == 2
            and x["minutes"] == 0
            and x["done"] is False
            and x["note"] is None
        ),
    )
    check(
        lab,
        "stable page with nested filtering",
        port,
        "GET",
        "/tasks?limit=1&offset=1",
        200,
        predicate=lambda x: (
            x["total"] == 2
            and x["items"][0]["id"] == 2
            and all(public(t) for t in x["items"])
        ),
    )
    check(
        lab,
        "read filtering",
        port,
        "GET",
        "/tasks/1",
        200,
        predicate=lambda x: x == first,
    )
    for name, patch, pred in [
        (
            "patch done preserves other fields",
            {"done": True},
            lambda x: (
                x["title"] == first["title"]
                and x["minutes"] == 25
                and x["note"] == "keep me"
                and x["done"] is True
            ),
        ),
        (
            "empty patch no-op",
            {},
            lambda x: x["done"] is True and x["note"] == "keep me",
        ),
        (
            "explicit false and zero",
            {"done": False, "minutes": 0},
            lambda x: (
                x["done"] is False and x["minutes"] == 0 and x["note"] == "keep me"
            ),
        ),
        ("replace note", {"note": "new"}, lambda x: x["note"] == "new"),
        ("clear note", {"note": None}, lambda x: x["note"] is None),
        ("empty string note", {"note": ""}, lambda x: x["note"] == ""),
        ("restore note", {"note": "keep me"}, lambda x: x["note"] == "keep me"),
        (
            "patch title spelling",
            {"title": "  NEW  "},
            lambda x: x["title"] == "  NEW  " and x["note"] == "keep me",
        ),
        (
            "patch valid placeholder value",
            {"title": "Untitled"},
            lambda x: x["title"] == "Untitled",
        ),
    ]:
        check(
            lab,
            name,
            port,
            "PATCH",
            "/tasks/1",
            200,
            patch,
            lambda x, pred=pred: public(x) and pred(x),
        )
    good = {"title": "Bad", "minutes": 1}
    invalid = [
        ("missing title", {"minutes": 1}),
        ("missing minutes", {"title": "Bad"}),
        ("empty title", {**good, "title": ""}),
        ("blank title", {**good, "title": " \t\n"}),
        ("unicode blank title", {**good, "title": "\u3000"}),
        ("long title", {**good, "title": "x" * 121}),
        ("numeric title", {**good, "title": 42}),
        ("null title", {**good, "title": None}),
        ("bool minutes", {**good, "minutes": True}),
        ("text minutes", {**good, "minutes": "25"}),
        ("float minutes", {**good, "minutes": 25.0}),
        ("negative minutes", {**good, "minutes": -1}),
        ("null minutes", {**good, "minutes": None}),
        ("integer done", {**good, "done": 1}),
        ("text done", {**good, "done": "false"}),
        ("null done", {**good, "done": None}),
        ("numeric note", {**good, "note": 1}),
        ("long note", {**good, "note": "x" * 1001}),
        ("client id", {**good, "id": 50}),
        ("client user id", {**good, "user_id": 7}),
        ("client internal field", {**good, "internal_tag": "spoof"}),
        ("unknown field", {**good, "typo": True}),
    ]
    for name, body in invalid:
        check(lab, name, port, "POST", "/tasks", 422, body)
    check(lab, "malformed JSON", port, "POST", "/tasks", 422, raw=b"{")
    before = check(lab, "before invalid patches", port, "GET", "/tasks/1", 200)
    for name, body in [
        ("null title", {"title": None}),
        ("null minutes", {"minutes": None}),
        ("null done", {"done": None}),
        ("blank title", {"title": " "}),
        ("bool minutes", {"minutes": True}),
        ("text minutes", {"minutes": "2"}),
        ("float minutes", {"minutes": 2.0}),
        ("negative minutes", {"minutes": -1}),
        ("text done", {"done": "false"}),
        ("invalid note", {"note": 1}),
        ("client id", {"id": 9}),
        ("client user id", {"user_id": 7}),
        ("long title", {"title": "x" * 121}),
        ("long note", {"note": "x" * 1001}),
        ("client internal field", {"internal_tag": "spoof"}),
        ("mixed valid invalid", {"done": True, "minutes": -1}),
    ]:
        check(lab, "patch " + name, port, "PATCH", "/tasks/1", 422, body)
    check(
        lab,
        "invalid writes change nothing",
        port,
        "GET",
        "/tasks/1",
        200,
        predicate=lambda x: x == before,
    )
    check(
        lab,
        "invalid creates consume no id",
        port,
        "POST",
        "/tasks",
        201,
        {"title": "x" * 120, "minutes": 1, "note": "x" * 1000},
        lambda x: x["id"] == 3 and public(x),
    )
    check(
        lab,
        "explicit create null note",
        port,
        "POST",
        "/tasks",
        201,
        {"title": "Nullable", "minutes": 1, "note": None},
        lambda x: x["note"] is None and public(x),
    )
    for name, path, status in [
        ("missing read", "/tasks/999", 404),
        ("bad id", "/tasks/nope", 422),
        ("zero id", "/tasks/0", 422),
        ("negative id", "/tasks/-1", 422),
        ("zero limit", "/tasks?limit=0", 422),
        ("large limit", "/tasks?limit=101", 422),
        ("bad limit", "/tasks?limit=nope", 422),
        ("negative offset", "/tasks?offset=-1", 422),
        ("bad offset", "/tasks?offset=nope", 422),
    ]:
        check(lab, name, port, "GET", path, status)
    check(
        lab,
        "empty later page",
        port,
        "GET",
        "/tasks?offset=99",
        200,
        predicate=lambda x: x["items"] == [] and x["total"] == 4,
    )
    check(lab, "missing patch", port, "PATCH", "/tasks/999", 404, {"done": True})
    check(lab, "delete", port, "DELETE", "/tasks/1", 204, predicate=lambda x: x == "")
    check(lab, "deleted read", port, "GET", "/tasks/1", 404)
    check(lab, "second delete", port, "DELETE", "/tasks/1", 404)
    check(
        lab,
        "remaining order",
        port,
        "GET",
        "/tasks",
        200,
        predicate=lambda x: (
            [t["id"] for t in x["items"]] == [2, 3, 4]
            and all(public(t) for t in x["items"])
        ),
    )
    check(
        lab,
        "OpenAPI body contract",
        port,
        "GET",
        "/openapi.json",
        200,
        predicate=lambda x: (
            x["components"]["schemas"]["TaskCreate"]["required"] == ["title", "minutes"]
            and not x["components"]["schemas"]["TaskPatch"].get("required")
            and x["components"]["schemas"]["TaskPatch"]["properties"]["title"]["type"]
            == "string"
        ),
    )
    stop(p)
    p, port, log = start(lab)
    check(
        lab,
        "restart loses data",
        port,
        "GET",
        "/tasks",
        200,
        predicate=lambda x: x == {"items": [], "limit": 20, "offset": 0, "total": 0},
    )
    check(lab, "restart loses old id", port, "GET", "/tasks/2", 404)
    check(
        lab,
        "restart reuses id",
        port,
        "POST",
        "/tasks",
        201,
        {"title": "New process", "minutes": 0},
        lambda x: x["id"] == 1,
    )
    stop(p)
    p, port, log = start(lab, "solutions.remaining_app:app")
    check(
        lab,
        "report empty",
        port,
        "GET",
        "/reports/remaining",
        200,
        predicate=lambda x: x == {"count": 0, "minutes": 0},
    )
    for title, minutes, done in [
        ("Zero", 0, False),
        ("Short", 15, False),
        ("Long", 90, False),
        ("Finished", 10, True),
    ]:
        check(
            lab,
            "report seed " + title,
            port,
            "POST",
            "/tasks",
            201,
            {"title": title, "minutes": minutes, "done": done},
        )
    check(
        lab,
        "report filter",
        port,
        "GET",
        "/reports/remaining?max_minutes=20",
        200,
        predicate=lambda x: x == {"count": 2, "minutes": 15},
    )
    check(
        lab,
        "report zero",
        port,
        "GET",
        "/reports/remaining?max_minutes=0",
        200,
        predicate=lambda x: x == {"count": 1, "minutes": 0},
    )
    check(lab, "report negative", port, "GET", "/reports/remaining?max_minutes=-1", 422)
    stop(p)
finally:
    for p, f, log in procs:
        stop(p)
        f.close()
    (OUT / "verification.json").write_text(
        json.dumps(
            {
                "date": "2026-09-28",
                "cases": cases,
                "counts": {
                    lab: sum(c["lab"] == lab for c in cases)
                    for lab in ["h03-first-fastapi", "h04-validation"]
                },
                "processes": [
                    {"pid": p.pid, "exit": p.returncode, "log": str(log)}
                    for p, f, log in procs
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
print("ALL PASSED", len(cases))
print("Evidence directory:", OUT)
