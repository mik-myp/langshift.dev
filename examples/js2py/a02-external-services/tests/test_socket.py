import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest

from lifecycle import managed_client
from service import HintService
from socket_lab import socket_scenario


@asynccontextmanager
async def tcp_probe(*, reply):
    """HTTP/1.1 peer that witnesses actual EOF, not just a close log line."""
    state = SimpleNamespace(reply=reply, entered=asyncio.Event(), eof=asyncio.Event())
    handlers, writers = [], set()

    async def handle(reader, writer):
        task = asyncio.current_task()
        handlers.append(task)
        writers.add(writer)
        try:
            await reader.readuntil(b"\r\n\r\n")
            state.entered.set()
            if state.reply:
                body = b'{"priority":"normal"}'
                writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
                             + f"Content-Length: {len(body)}\r\n".encode()
                             + b"Connection: keep-alive\r\n\r\n" + body)
                await writer.drain()
            assert await reader.read() == b""
            state.eof.set()
        finally:
            writer.close()
            await writer.wait_closed()
            writers.discard(writer)

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    state.origin = f"http://127.0.0.1:{server.sockets[0].getsockname()[1]}"
    try:
        yield state
    finally:
        server.close()
        # Close accepted peers BEFORE wait_closed: a deliberately leaked client
        # must make the assertion fail, not hang the test fixture teardown.
        for writer in tuple(writers):
            writer.close()
        await asyncio.wait_for(server.wait_closed(), 5)
        if handlers:
            await asyncio.wait_for(asyncio.gather(*handlers), 5)


@pytest.mark.parametrize("exit_mode", ["normal", "exception", "cancel"])
def test_real_connection_released_for_every_owner_exit(exit_mode):
    async def scenario():
        async with tcp_probe(reply=exit_mode != "cancel") as peer:
            clients = []
            async def owner():
                async with managed_client(peer.origin) as client:
                    clients.append(client)
                    response = await client.get("/hint")
                    assert response.status_code == 200
                    if exit_mode == "exception":
                        raise LookupError("synthetic failure inside resource scope")
            task = asyncio.create_task(owner())
            try:
                async with asyncio.timeout(5):
                    await peer.entered.wait()
                    if exit_mode == "cancel":
                        task.cancel()
                        with pytest.raises(asyncio.CancelledError):
                            await task
                    elif exit_mode == "exception":
                        with pytest.raises(LookupError):
                            await task
                    else:
                        await task
                    await peer.eof.wait()  # The actual remote socket saw closure.
                assert clients[0].is_closed
                with pytest.raises(RuntimeError, match="closed"):
                    await clients[0].get("/hint")
            finally:
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
    asyncio.run(scenario())


def test_real_cancel_releases_attempt_but_not_application_client():
    async def scenario():
        async with tcp_probe(reply=False) as peer:
            async with managed_client(peer.origin) as client:
                service = HintService(client, concurrency=1, deadline=5)
                task = asyncio.create_task(service.hint())
                try:
                    async with asyncio.timeout(5):
                        await peer.entered.wait()
                        task.cancel()
                        with pytest.raises(asyncio.CancelledError):
                            await task
                        await peer.eof.wait()
                        assert service.active == 0 and not client.is_closed
                        peer.reply = True
                        assert (await service.hint())["state"] == "available"
                        assert service.peak == 1
                finally:
                    task.cancel()
                    await asyncio.gather(task, return_exceptions=True)
    asyncio.run(scenario())


def test_two_real_servers_and_fault_isolation():
    asyncio.run(socket_scenario())
