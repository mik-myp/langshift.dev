#!/usr/bin/env python3
"""Standalone maintainer verification for H05/H06 only; no shared registration.

Run with CPython 3.13.15/uv 0.12.13 available. All service processes listen only
on 127.0.0.1 and are terminated in finally. Labs are copied by explicit allowlist
into temporary directories, so tests cannot accidentally import the sibling lab.
Browser CORS enforcement is a separate real-browser check, not claimed here.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import tempfile
import time
import tomllib
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
LAB_ROOT = ROOT / "examples/js2py"
ENV = os.environ.copy()
ENV["PATH"] = str(Path.home() / ".local/bin") + os.pathsep + ENV.get("PATH", "")
ENV.setdefault("UV_PYTHON_INSTALL_DIR", "/tmp/langshift-js2py-python-20260928")
ENV.setdefault("UV_CACHE_DIR", "/tmp/langshift-js2py-uv-cache-20260928")
for key in [
    "TASKS_APP_NAME",
    "TASKS_MAX_PAGE_SIZE",
    "PYTHONPATH",
    "PYTHONHOME",
    "VIRTUAL_ENV",
    "UV_PROJECT_ENVIRONMENT",
    "UV_ACTIVE",
    "UV_PYTHON",
]:
    ENV.pop(key, None)
ENV["UV_NO_CONFIG"] = "1"


def command(args, cwd, *, env=None, expected=0):
    print("RUN", " ".join(map(str, args)), "IN", cwd, flush=True)
    result = subprocess.run(
        args,
        cwd=cwd,
        env=ENV if env is None else env,
        text=True,
        capture_output=True,
        timeout=150,
    )
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    assert result.returncode == expected, (args, result.returncode, expected)
    return result.stdout + result.stderr


def request(port, path, *, method="GET", payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = Request(
        f"http://127.0.0.1:{port}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        response = urlopen(req, timeout=2)
    except HTTPError as error:
        response = error
    with response:
        body = response.read()
        return response.status, json.loads(body) if body else None


def stage(lab, destination):
    source = LAB_ROOT / lab
    files = json.loads((LAB_ROOT / f"{lab}-files.json").read_text())
    assert len(files) == len(set(files))
    destination.mkdir()
    for name in files:
        relative = Path(name)
        assert not relative.is_absolute() and ".." not in relative.parts
        assert not any(
            part in {".venv", "__pycache__", ".pytest_cache", ".env"}
            for part in relative.parts
        )
        assert not any(part.startswith(".env.") for part in relative.parts)
        path = source / relative
        assert path.is_file() and not path.is_symlink(), path
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    config = tomllib.loads((destination / "pyproject.toml").read_text())
    assert config["project"]["requires-python"] == ">=3.13,<3.14"
    assert config["tool"]["uv"]["package"] is False
    lock = tomllib.loads((destination / "uv.lock").read_text())
    for package in lock["package"]:
        if "registry" in package["source"]:
            assert package["source"]["registry"] == "https://pypi.org/simple"
        for artifact in [package.get("sdist"), *package.get("wheels", [])]:
            if artifact:
                assert urlparse(artifact["url"]).hostname == "files.pythonhosted.org"
                assert artifact["hash"].startswith("sha256:")
    return files


def real_server(lab, *, factory="task_api.main:create_app", summary=False, cap=None):
    port = 0  # Let our child bind atomically; read its own announced port.
    child_env = ENV | {"TASKS_APP_NAME": "Live acceptance"}
    if cap is not None:
        child_env["TASKS_MAX_PAGE_SIZE"] = str(cap)
    with tempfile.TemporaryFile(mode="w+t") as log:
        args = [
            str(lab / ".venv/bin/python"),
            "-m",
            "uvicorn",
            factory,
            "--factory",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ]
        print("SERVER", " ".join(args), flush=True)
        process = subprocess.Popen(args, cwd=lab, env=child_env, stdout=log, stderr=log)
        try:
            deadline = time.monotonic() + 15
            while True:
                if process.poll() is not None:
                    raise AssertionError("Owned server exited before readiness")
                announced = os.pread(log.fileno(), 100_000, 0).decode("utf-8")
                match = re.search(
                    r"Uvicorn running on http://127\.0\.0\.1:(\d+)", announced
                )
                if match:
                    port = int(match.group(1))
                    try:
                        if request(port, "/health") == (200, {"status": "ok"}):
                            break
                    except (URLError, TimeoutError, ConnectionError):
                        pass
                assert time.monotonic() < deadline, "Local server readiness timeout"
                time.sleep(0.05)
            assert (
                request(port, "/openapi.json")[1]["info"]["title"] == "Live acceptance"
            )
            if cap is not None:
                assert request(port, "/tasks?limit=21") == (
                    422,
                    {"detail": "limit exceeds TASKS_MAX_PAGE_SIZE"},
                )
                assert request(port, "/tasks?limit=20")[0] == 200
            else:
                client_args = [
                    str(lab / ".venv/bin/python"),
                    "live_client.py",
                    "--port",
                    str(port),
                ]
                if summary:
                    client_args.append("--summary")
                command(client_args, lab)
                if lab.name == "h06-api-testing":
                    command(
                        [
                            str(lab / ".venv/bin/python"),
                            "live_httpx.py",
                            "--port",
                            str(port),
                        ],
                        lab,
                    )
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            log.seek(0)
            text = log.read()
            if process.returncode not in [0, -15]:
                print(text)
        assert text.count("TRACE acquire") == text.count("closed=True"), text
        if cap is None:
            assert "TRACE release GET /tasks/99999 closed=True" in text
        assert process.poll() is not None
        with socket.socket() as sock:
            assert sock.connect_ex(("127.0.0.1", port)) != 0, (
                "Owned server port still open"
            )
        print(
            "SERVER PASS: acquisition/cleanup balanced, process stopped, port closed",
            flush=True,
        )


# This instrumentation intentionally belongs to the maintainer script, not the
# synchronous reader curriculum. Inspect actual ASGI send, not client-return time.
SCOPE_PROBE = r"""
import contextlib
import io
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from task_api.dependencies import RequestTrace, request_trace
for scope in ["function", "request"]:
    for failing in [False, True]:
        app = FastAPI()
        output = io.StringIO()
        observations = []
        @app.get("/probe")
        def probe(trace: RequestTrace = Depends(request_trace, scope=scope)):
            trace.mark("handler")
            if failing:
                raise HTTPException(409, "controlled failure")
            return {"ok": True}
        class ObserveSend:
            async def __call__(self, asgi_scope, receive, send):
                async def observed_send(message):
                    if message["type"].startswith("http.response."):
                        observations.append((message["type"], "closed=True" in output.getvalue()))
                    await send(message)
                await app(asgi_scope, receive, observed_send)
        with contextlib.redirect_stdout(output):
            with TestClient(ObserveSend()) as client:
                response = client.get("/probe")
        assert response.status_code == (409 if failing else 200)
        assert output.getvalue().count("TRACE acquire") == 1
        assert output.getvalue().count("closed=True") == 1
        expected = scope == "function" or failing
        assert observations == [("http.response.start", expected), ("http.response.body", expected)]
        print("SCOPE", scope, "handled-error" if failing else "success", observations)
print("SCOPE PASS: four actual ASGI send-order cases")
"""


def main():
    assert "uv 0.12.13" in command(["uv", "--version"], ROOT)
    results = {}
    with tempfile.TemporaryDirectory(prefix="js2py-h05-h06-") as directory:
        for name in ["h05-dependencies", "h06-api-testing"]:
            lab = Path(directory) / name
            files = stage(name, lab)
            command(["uv", "sync", "--locked"], lab)
            python = str(lab / ".venv/bin/python")
            assert "Python 3.13.15" in command([python, "--version"], lab)
            counts = []
            for target in ["tests", "solutions"]:
                result = command([python, "-m", "pytest", "-q", target], lab)
                counts.append(int(re.search(r"(\d+) passed", result)[1]))
            assert (
                counts
                == {"h05-dependencies": [17, 2], "h06-api-testing": [48, 3]}[name]
            ), counts
            for env_add, expected_text in [
                ({}, "TASKS_APP_NAME is required and must not be blank"),
                (
                    {"TASKS_APP_NAME": "Live", "TASKS_MAX_PAGE_SIZE": "bad"},
                    "TASKS_MAX_PAGE_SIZE must be an integer from 20 to 100",
                ),
            ]:
                result = command(
                    [
                        python,
                        "-m",
                        "uvicorn",
                        "task_api.main:create_app",
                        "--factory",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        "0",
                    ],
                    lab,
                    env=ENV | env_add,
                    expected=1,
                )
                assert expected_text in result
            real_server(lab)
            real_server(lab, cap=20)
            if name == "h05-dependencies":
                real_server(
                    lab, factory="solutions.summary:create_summary_app", summary=True
                )
            else:
                expected = command(
                    [
                        python,
                        "-m",
                        "pytest",
                        "-q",
                        "experiments/test_fixture_failure.py",
                    ],
                    lab,
                    expected=1,
                )
                assert "1 failed, 1 passed" in expected
                command([python, "-c", SCOPE_PROBE], lab)
                # A second fresh pytest process must not inherit previous overrides/state.
                command([python, "-m", "pytest", "-q", "tests"], lab)
            # Prove that the independent/state tests reject controlled regressions.
            if name == "h05-dependencies":
                target = lab / "task_api/main.py"
                original = target.read_text()
                damaged = original.replace(
                    "\n\ndef create_app",
                    "\n\nshared_store = MemoryStore()\n\ndef create_app",
                )
                damaged = damaged.replace(
                    "app.state.store = MemoryStore()", "app.state.store = shared_store"
                )
                case = "tests/test_basics.py::test_factory_owns_state"
            else:
                target = lab / "task_api/store.py"
                original = target.read_text()
                damaged = original.replace(
                    "payload.model_dump(exclude_unset=True)", "payload.model_dump()"
                )
                case = "solutions/test_independent.py::test_empty_patch_preserves_non_default_values"
            assert damaged != original
            try:
                target.write_text(damaged)
                result = command([python, "-m", "pytest", "-q", case], lab, expected=1)
                assert "1 failed" in result
            finally:
                target.write_text(original)
            command([python, "-m", "pytest", "-q", case], lab)
            print("MUTATION PASS: defect detected and original restored", flush=True)
            results[name] = {
                "allowlisted_files": len(files),
                "pytest_passed": counts,
                "real_http": True,
                "configuration_failures": 2,
                "owned_processes_stopped": True,
            }
    print("H05/H06 VERIFICATION", json.dumps(results, sort_keys=True))


if __name__ == "__main__":
    main()
