"""Test-only fault service. Never mount /control in a real application."""
import asyncio
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel


class Control(BaseModel):
    mode: Literal["ok", "unavailable", "flaky", "malformed", "wrongshape", "oversized", "slow", "hold"]


def create_fault_app():
    app = FastAPI()
    app.state.mode = "ok"
    app.state.calls = 0
    app.state.client_ports = set()
    app.state.entered = asyncio.Event()
    app.state.release = asyncio.Event()

    @app.post("/control")
    async def control(data: Control):
        app.state.mode = data.mode
        app.state.calls = 0
        app.state.entered.clear()
        app.state.release.clear()
        return {"mode": data.mode}

    @app.get("/hint")
    async def hint(request: Request):
        app.state.client_ports.add(request.client.port)
        app.state.calls += 1
        mode = app.state.mode
        app.state.entered.set()
        if mode == "hold":
            await app.state.release.wait()
            return JSONResponse({"error": "synthetic outage"}, status_code=503)
        if mode == "slow":
            await asyncio.sleep(0.4)  # Exceeds configured read-idle timeout.
        if mode == "unavailable" or (mode == "flaky" and app.state.calls == 1):
            return JSONResponse({"error": "synthetic outage"}, status_code=503)
        if mode == "malformed":
            return Response("not-json", media_type="application/json")
        if mode == "wrongshape":
            return JSONResponse({"priority": "urgent", "internal": "synthetic-only"})
        if mode == "oversized":
            return JSONResponse({"priority": "normal", "padding": "x" * 1500})
        return {"priority": "normal"}

    return app
