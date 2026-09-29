import asyncio
import json
import subprocess
import sys

import anyio
import httpx
import pytest

from app import create_app
from lifecycle import managed_client, validate_origin
from service import HintService

ORIGIN = "http://127.0.0.1:8766"


def reply(body=b'{"priority":"normal"}', *, status=200, headers=None):
    return httpx.Response(status, headers=headers or {"content-type": "application/json"},
                          stream=httpx.ByteStream(body))


@pytest.mark.parametrize("kind,expected,attempts", [
    ("ok", "available", 1), ("flaky", "available", 2),
    ("503", "unavailable", 2), ("429", "unavailable", 1),
    ("401", "unavailable", 1), ("redirect", "unavailable", 1),
    ("malformed", "unavailable", 1), ("shape", "unavailable", 1),
    ("oversized", "unavailable", 1), ("html", "unavailable", 1),
    ("encoded", "unavailable", 1), ("connect", "unavailable", 2),
    ("read", "unavailable", 2), ("pool", "unavailable", 1),
])
def test_contract_and_bounded_retry(kind, expected, attempts):
    async def scenario():
        calls = []
        def handler(request):
            calls.append(request)
            assert request.url.path == "/hint" and request.method == "GET"
            assert request.content == b"" and not request.url.query
            assert "authorization" not in request.headers
            if kind in {"connect", "read", "pool"}:
                error = {"connect": httpx.ConnectError, "read": httpx.ReadTimeout,
                         "pool": httpx.PoolTimeout}[kind]
                raise error("FAKE_PRIVATE_DETAIL", request=request)
            if kind == "flaky" and len(calls) == 1:
                return reply(status=503)
            if kind.isdigit():
                return reply(status=int(kind))
            if kind == "redirect":
                return reply(status=302, headers={"location": "https://example.invalid"})
            if kind == "malformed":
                return reply(b"not-json")
            if kind == "shape":
                return reply(b'{"priority":"urgent","credential":"FAKE"}')
            if kind == "oversized":
                return reply(b"x" * 1025)
            if kind == "html":
                return reply(headers={"content-type": "text/html"})
            if kind == "encoded":
                return reply(headers={"content-type": "application/json", "content-encoding": "gzip"})
            return reply()
        async with managed_client(ORIGIN, transport=httpx.MockTransport(handler)) as client:
            service = HintService(client, backoff=0)
            result = await service.hint()
            assert result == {"state": expected, "priority": "normal" if expected == "available" else None}
            assert service.attempts == len(calls) == attempts
            assert service.active == 0
        assert client.is_closed
    asyncio.run(scenario())


def test_deadline_includes_backoff():
    async def scenario():
        async with managed_client(ORIGIN, transport=httpx.MockTransport(lambda r: reply(status=503))) as client:
            service = HintService(client, deadline=0.01, backoff=1)
            assert (await service.hint())["state"] == "unavailable"
            assert service.attempts == 1 and service.active == 0
    asyncio.run(scenario())


def test_deadline_includes_semaphore_wait_and_sends_nothing():
    async def scenario():
        async with managed_client(ORIGIN, transport=httpx.MockTransport(lambda r: reply())) as client:
            service = HintService(client, concurrency=1, deadline=0.01)
            await service.slots.acquire()
            try:
                assert (await service.hint())["state"] == "unavailable"
                assert service.attempts == 0 and service.active == 0
                assert service.slots.locked()
            finally:
                service.slots.release()
    asyncio.run(scenario())


def test_cancel_is_propagated_and_capacity_is_reusable():
    async def scenario():
        entered, release = asyncio.Event(), asyncio.Event()
        async def handler(request):
            entered.set()
            await release.wait()
            return reply()
        async with managed_client(ORIGIN, transport=httpx.MockTransport(handler)) as client:
            service = HintService(client, concurrency=1)
            task = asyncio.create_task(service.hint())
            try:
                await entered.wait()
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task
                assert service.active == 0 and service.attempts == 1
                release.set()
                assert (await service.hint())["state"] == "available"
            finally:
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
    asyncio.run(scenario())


def test_anyio_cancel_scope_does_not_interrupt_awaited_cleanup():
    class ClosingTransport(httpx.AsyncBaseTransport):
        closed = False
        async def aclose(self):
            await anyio.sleep(0)  # Without shielding this checkpoint is cancelled.
            self.closed = True
    async def scenario():
        transport = ClosingTransport()
        with anyio.CancelScope() as scope:
            async with managed_client(ORIGIN, transport=transport) as client:
                scope.cancel()
                await anyio.sleep(0)
        assert transport.closed and client.is_closed
    anyio.run(scenario, backend="asyncio")


def test_asgi_lifespan_reuses_one_client_and_core_does_not_call_upstream():
    async def scenario():
        requests = []
        def handler(request):
            requests.append(request)
            return reply(status=503)
        app = create_app(transport=httpx.MockTransport(handler))
        # ASGITransport does not run lifespan. The test owns it explicitly.
        async with app.router.lifespan_context(app):
            owned = app.state.client
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test", trust_env=False) as caller:
                assert (await caller.post("/tasks", json={"title": " "})).status_code == 422
                created = await caller.post("/tasks", json={"title": "Synthetic only"})
                assert created.status_code == 201
                assert (await caller.get("/tasks/1")).status_code == 200
                assert requests == []
                for _ in range(2):
                    assert (await caller.get("/tasks/1/hint")).json()["state"] == "unavailable"
                    assert app.state.client is owned
                assert len(requests) == 4
                assert (await caller.patch("/tasks/1", json={"title": "Changed"})).status_code == 200
                assert (await caller.delete("/tasks/1")).status_code == 204
                assert (await caller.get("/tasks/1")).status_code == 404
                assert (await caller.get("/tasks/1/hint")).status_code == 404
                assert len(requests) == 4
        assert owned.is_closed
    asyncio.run(scenario())


@pytest.mark.parametrize("origin", [
    "https://example.invalid", "http://localhost:8766", "http://127.0.0.1:0",
    "http://demo:FAKE@127.0.0.1:8766", "http://127.0.0.1:8766/?token=FAKE",
])
def test_origin_allowlist_and_redacted_errors(origin):
    with pytest.raises(ValueError) as error:
        validate_origin(origin)
    assert origin not in str(error.value) and "FAKE" not in str(error.value)


@pytest.mark.parametrize("module,needle", [
    ("errors.config", "value omitted"), ("errors.untrusted", "ValidationError"),
])
def test_real_diagnostic_commands(module, needle):
    run = subprocess.run([sys.executable, "-m", module], capture_output=True, text=True, timeout=10)
    assert run.returncode == 1 and needle in run.stderr
    if module == "errors.config":
        # The traceback includes the source line containing the FAKE fixture. The
        # exception's message is redacted; never publish raw tracebacks to clients.
        assert "FAKE" not in run.stderr.strip().splitlines()[-1]


def test_concurrency_bound_with_observable_admission():
    async def scenario():
        admitted = [asyncio.Event(), asyncio.Event(), asyncio.Event()]
        release = asyncio.Event()
        calls = 0
        async def handler(request):
            nonlocal calls
            index = calls
            calls += 1
            admitted[index].set()
            await release.wait()
            return reply()
        async with managed_client(ORIGIN, transport=httpx.MockTransport(handler)) as client:
            service = HintService(client, concurrency=2, deadline=5)
            tasks = [asyncio.create_task(service.hint()) for _ in range(3)]
            try:
                async with asyncio.timeout(5):
                    await admitted[0].wait()
                    await admitted[1].wait()
                    assert service.active == 2 and calls == 2 and not admitted[2].is_set()
                    tasks[0].cancel()
                    with pytest.raises(asyncio.CancelledError):
                        await tasks[0]
                    await admitted[2].wait()
                    assert service.active == 2 and calls == 3
                    release.set()
                    assert all(x["state"] == "available" for x in await asyncio.gather(*tasks[1:]))
                assert service.active == 0 and service.peak == 2
            finally:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
    asyncio.run(scenario())
