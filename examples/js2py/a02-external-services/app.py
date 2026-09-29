from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field, field_validator

from lifecycle import DEFAULT_UPSTREAM, managed_client, validate_origin
from service import HintService


class TaskInput(BaseModel):
    title: str = Field(min_length=1, max_length=80)

    @field_validator("title")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("title must not be blank")
        return value.strip()


def create_app(origin=DEFAULT_UPSTREAM, *, transport=None):
    origin = validate_origin(origin)

    @asynccontextmanager
    async def lifespan(app):
        async with managed_client(origin, transport=transport) as client:
            app.state.client = client
            app.state.hints = HintService(client)
            app.state.tasks = {}
            app.state.next_id = 1
            yield

    app = FastAPI(lifespan=lifespan)

    def require_task(task_id):
        task = app.state.tasks.get(task_id)
        if task is None:
            raise HTTPException(404, "task not found")
        return task

    @app.get("/health/live")
    async def live():
        return {"status": "ok"}

    @app.post("/tasks", status_code=201)
    async def create_task(data: TaskInput):
        task_id = app.state.next_id
        app.state.next_id += 1
        task = {"id": task_id, "title": data.title}
        app.state.tasks[task_id] = task
        return task

    @app.get("/tasks/{task_id}")
    async def read_task(task_id: int):
        return require_task(task_id)

    @app.patch("/tasks/{task_id}")
    async def update_task(task_id: int, data: TaskInput):
        task = require_task(task_id)
        task["title"] = data.title
        return task

    @app.delete("/tasks/{task_id}", status_code=204)
    async def delete_task(task_id: int):
        require_task(task_id)
        del app.state.tasks[task_id]
        return Response(status_code=204)

    @app.get("/tasks/{task_id}/hint")
    async def optional_hint(task_id: int):
        require_task(task_id)
        return {"task_id": task_id, **await app.state.hints.hint()}

    return app
