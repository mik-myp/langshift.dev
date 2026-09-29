"""Real TCP, two Uvicorn servers, ephemeral loopback ports, no subprocess killing."""
import asyncio
import socket
from contextlib import asynccontextmanager

import httpx
import uvicorn

from app import create_app
from faults import create_fault_app


@asynccontextmanager
async def serve(app):
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    origin = f"http://127.0.0.1:{listener.getsockname()[1]}"
    server = uvicorn.Server(uvicorn.Config(
        app, host="127.0.0.1", log_level="critical", access_log=False,
        lifespan="on", loop="asyncio", http="h11", ws="none",
    ))
    task = asyncio.create_task(server.serve(sockets=[listener]))
    try:
        async with asyncio.timeout(5):
            while not server.started:
                if task.done():
                    await task
                    raise RuntimeError("local server exited before startup")
                await asyncio.sleep(0.01)
        yield origin
    finally:
        server.should_exit = True  # Only our own Server object.
        try:
            await asyncio.wait_for(task, timeout=5)
        finally:
            listener.close()


async def socket_scenario():
    fault = create_fault_app()
    async with serve(fault) as upstream:
        app = create_app(upstream)
        async with serve(app) as api:
            async with httpx.AsyncClient(timeout=3, trust_env=False) as caller:
                response = await caller.post(f"{api}/tasks", json={"title": "Synthetic task"})
                assert response.status_code == 201
                task_id = response.json()["id"]
                path = f"{api}/tasks/{task_id}"
                assert (await caller.get(f"{path}/hint")).json()["state"] == "available"
                assert (await caller.get(f"{path}/hint")).json()["state"] == "available"
                assert len(fault.state.client_ports) == 1
                print("socket: normal hint available; upstream connection reused")
                for mode in ["unavailable", "malformed", "wrongshape", "oversized", "slow"]:
                    assert (await caller.post(f"{upstream}/control", json={"mode": mode})).status_code == 200
                    response = await caller.get(f"{path}/hint")
                    assert response.status_code == 200
                    assert response.json() == {"task_id": task_id, "state": "unavailable", "priority": None}
                    assert (await caller.get(path)).status_code == 200
                    print(f"socket: {mode} -> unavailable; core read ok")
                # Gate-based isolation proof: generous guards, not a speed test.
                app.state.client.timeout = httpx.Timeout(10)
                app.state.hints.deadline = 10
                await caller.post(f"{upstream}/control", json={"mode": "hold"})
                waiting = asyncio.create_task(caller.get(f"{path}/hint"))
                try:
                    async with asyncio.timeout(3):
                        await fault.state.entered.wait()
                    assert not waiting.done()
                    # These finish while the upstream is still gated, not by a ms threshold.
                    extra = await caller.post(f"{api}/tasks", json={"title": "Created during outage"})
                    assert extra.status_code == 201
                    assert (await caller.patch(path, json={"title": "Still usable"})).status_code == 200
                    assert (await caller.get(path)).json()["title"] == "Still usable"
                    assert (await caller.delete(path)).status_code == 204
                    assert (await caller.get(path)).status_code == 404
                    assert not waiting.done()
                    print("socket: core create/update/read/delete finished while upstream held")
                finally:
                    fault.state.release.set()
                    await waiting
        assert app.state.client.is_closed
        print("socket: lifespan client closed")


if __name__ == "__main__":
    asyncio.run(socket_scenario())
