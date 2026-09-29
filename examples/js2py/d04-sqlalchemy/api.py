"""Local teaching API: identity is supplied, NOT authenticated. Never deploy this."""
from contextlib import asynccontextmanager
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db import make_engine, session_factory
from models import Project
from services import create_project, create_task, list_tasks


class ProjectInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    owner_id: int = Field(gt=0)  # Replaced by server-verified identity in S chapters.

    @field_validator("name")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("name must not be blank")
        return value


class TaskInput(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    created_by: int = Field(gt=0)
    minutes: int = Field(default=0, ge=0)
    status: Literal["todo", "doing", "done"] = "todo"
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("title")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("title must not be blank")
        return value


class ProjectOutput(BaseModel):
    id: int
    name: str
    created_by: int


class TaskOutput(TaskInput):
    id: int
    project_id: int


def create_app(engine):
    sessions = session_factory(engine)

    @asynccontextmanager
    async def lifespan(app):
        # ASGI lifecycle wrapper only; all database operations below are synchronous.
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(lifespan=lifespan)

    def get_session():
        # This boundary closes on success AND failure; it never secretly commits.
        with sessions() as session:
            yield session

    @app.post("/projects", response_model=ProjectOutput, status_code=201)
    def post_project(body: ProjectInput, session: Annotated[Session, Depends(get_session)]):
        try:
            with session.begin():
                result = create_project(session, body.name, body.owner_id)
            # COMMIT has succeeded before the endpoint reports success.
            return result
        except IntegrityError as error:
            raise HTTPException(409, "Database rule rejected this write") from error

    @app.get("/projects", response_model=list[ProjectOutput])
    def get_projects(session: Annotated[Session, Depends(get_session)]):
        # Read also autobegins a transaction; closing the Session ends it.
        return [{"id": p.id, "name": p.name, "created_by": p.created_by}
                for p in session.scalars(select(Project).order_by(Project.id))]

    @app.post("/projects/{project_id}/tasks", response_model=TaskOutput, status_code=201)
    def post_task(project_id: int, body: TaskInput,
                  session: Annotated[Session, Depends(get_session)]):
        try:
            with session.begin():
                if session.get(Project, project_id) is None:
                    raise HTTPException(404, "Project not found")
                result = create_task(session, project_id, **body.model_dump())
            return result
        except IntegrityError as error:
            raise HTTPException(409, "Database rule rejected this write") from error

    @app.get("/projects/{project_id}/tasks", response_model=list[TaskOutput])
    def get_tasks(project_id: int, session: Annotated[Session, Depends(get_session)],
                  status: Literal["todo", "doing", "done"] | None = None,
                  limit: Annotated[int, Query(ge=1, le=100)] = 20,
                  offset: Annotated[int, Query(ge=0)] = 0):
        if session.get(Project, project_id) is None:
            raise HTTPException(404, "Project not found")
        return list_tasks(session, project_id, status, limit, offset)

    return app


def application():
    return create_app(make_engine())
