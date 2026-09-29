from fastapi import FastAPI, Header, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from db import SessionLocal, SESSION_TTL, EXPECTED_REVISION, bounded_seconds
from reliable import create_task_once, parse_key
IDEMPOTENCY_TTL = bounded_seconds("IDEMPOTENCY_TTL_SECONDS", 86400, 60, 604800)
from schemas import LoginInput, PasswordChange, TokenResponse, UserPublic
from security import authenticate, change_password, login, utc_now, audit

app = FastAPI(title="Security Foundations")


@app.exception_handler(RequestValidationError)
def sanitized_validation(request, error):
    # This framework callback returns only a deliberately sanitized JSON shape.
    # Do not return error.errors(), body, input, msg, ctx or submitted extra keys.
    safe_names = {"body", "path", "query", "header", "login", "password", "current_password",
        "new_password", "project_id", "task_id", "user_id", "name", "title", "description",
        "status", "minutes", "priority", "due_at", "limit", "offset", "idempotency-key"}
    details = [{"loc": [part if isinstance(part, int) or part in safe_names else "field"
                        for part in item["loc"]], "type": item["type"]}
               for item in error.errors()]
    return JSONResponse(status_code=422, content={"detail": details})


@app.exception_handler(IntegrityError)
def sanitized_integrity(request, error):
    # The Session.begin context has already rolled the failed transaction back.
    return JSONResponse(status_code=409, content={"detail": "Operation conflicts with stored data"})


@app.exception_handler(SQLAlchemyError)
def sanitized_database_failure(request, error):
    # Driver text can contain values even with SQLAlchemy hide_parameters=True.
    # Expected database failures are handled without logging exception repr/traceback.
    audit.error("database_operation_failed")
    return JSONResponse(status_code=503, content={"detail": "Service temporarily unavailable"})


@app.get("/health/live")
def live():
    return {"status": "ok"}


@app.get("/health/ready")
def ready():
    try:
        with SessionLocal.begin() as session:
            session.execute(text("SELECT 1"))
            revision = session.scalar(text("SELECT version_num FROM alembic_version"))
            if revision != EXPECTED_REVISION:
                return JSONResponse(status_code=503, content={"status": "unavailable"})
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return {"status": "ready"}


@app.post("/auth/token", response_model=TokenResponse)
def issue_token(payload: LoginInput, response: Response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    with SessionLocal.begin() as session:
        result = login(session, payload.login, payload.password.get_secret_value(), SESSION_TTL)
    return result


@app.get("/users/me", response_model=UserPublic)
def me(authorization: str | None = Header(default=None)):
    with SessionLocal.begin() as session:
        user, credential = authenticate(session, authorization)
        result = UserPublic.model_validate(user)
    return result


@app.post("/users/me/password", status_code=204)
def update_password(payload: PasswordChange, authorization: str | None = Header(default=None)):
    with SessionLocal.begin() as session:
        user, credential = authenticate(session, authorization, change_user=True)
        change_password(session, user, payload.current_password.get_secret_value(),
                        payload.new_password.get_secret_value())
    return Response(status_code=204)


@app.post("/auth/logout", status_code=204)
def logout(authorization: str | None = Header(default=None)):
    with SessionLocal.begin() as session:
        user, credential = authenticate(session, authorization, change_session=True)
        credential.revoked_at = utc_now()
    return Response(status_code=204)


@app.post("/auth/logout-all", status_code=204)
def logout_all(authorization: str | None = Header(default=None)):
    with SessionLocal.begin() as session:
        user, credential = authenticate(session, authorization, change_user=True)
        user.auth_version += 1
    return Response(status_code=204)


from fastapi import Path, Query
from sqlalchemy import func, select
from models import Project, ProjectMember, Task
from schemas import (MemberInput, MemberPublic, ProjectInput, ProjectPage, ProjectPublic,
                     TaskInput, TaskPage, TaskPatch, TaskPublic)
from authorization import (add_member, create_project, create_task, delete_project, find_task,
                           guard_project, may_edit_task, patch_task, remove_member, require_owner)


@app.post("/projects", response_model=ProjectPublic, status_code=201)
def new_project(payload: ProjectInput, authorization: str | None = Header(default=None)):
    with SessionLocal.begin() as session:
        actor, credential = authenticate(session, authorization)
        result = ProjectPublic.model_validate(create_project(session, actor.id, payload.name))
    return result


@app.get("/projects", response_model=ProjectPage)
def projects(limit: int = Query(default=20, ge=1, le=100), offset: int = Query(default=0, ge=0),
             authorization: str | None = Header(default=None)):
    with SessionLocal.begin() as session:
        actor, credential = authenticate(session, authorization)
        condition = ProjectMember.user_id == actor.id
        statement = select(Project).join(ProjectMember).where(condition)
        records = session.scalars(statement.order_by(Project.id).limit(limit).offset(offset)).all()
        total = session.scalar(select(func.count()).select_from(Project).join(ProjectMember).where(condition))
        result = {"items": [ProjectPublic.model_validate(r) for r in records],
                  "limit": limit, "offset": offset, "total": total}
    return result


@app.get("/projects/{project_id}", response_model=ProjectPublic)
def project_detail(project_id: int = Path(gt=0, le=9223372036854775807),
                   authorization: str | None = Header(default=None)):
    with SessionLocal.begin() as session:
        actor, credential = authenticate(session, authorization)
        project, member = guard_project(session, actor.id, project_id)
        result = ProjectPublic.model_validate(project)
    return result


@app.patch("/projects/{project_id}", response_model=ProjectPublic)
def rename_project(payload: ProjectInput, project_id: int = Path(gt=0, le=9223372036854775807),
                   authorization: str | None = Header(default=None)):
    with SessionLocal.begin() as session:
        actor, credential = authenticate(session, authorization)
        project, member = guard_project(session, actor.id, project_id, exclusive=True)
        require_owner(member)
        project.name = payload.name
        session.flush()
        result = ProjectPublic.model_validate(project)
    return result


@app.delete("/projects/{project_id}", status_code=204)
def erase_project(project_id: int = Path(gt=0, le=9223372036854775807),
                  authorization: str | None = Header(default=None)):
    with SessionLocal.begin() as session:
        actor, credential = authenticate(session, authorization)
        project, member = guard_project(session, actor.id, project_id, exclusive=True)
        require_owner(member)
        delete_project(session, project)
    return Response(status_code=204)


@app.get("/projects/{project_id}/members", response_model=list[MemberPublic])
def members(project_id: int = Path(gt=0, le=9223372036854775807),
            authorization: str | None = Header(default=None)):
    with SessionLocal.begin() as session:
        actor, credential = authenticate(session, authorization)
        guard_project(session, actor.id, project_id)
        records = session.scalars(select(ProjectMember).where(ProjectMember.project_id == project_id)
                                  .order_by(ProjectMember.user_id)).all()
        result = [MemberPublic.model_validate(record) for record in records]
    return result


@app.post("/projects/{project_id}/members", response_model=MemberPublic, status_code=201)
def invite(payload: MemberInput, project_id: int = Path(gt=0, le=9223372036854775807),
           authorization: str | None = Header(default=None)):
    with SessionLocal.begin() as session:
        actor, credential = authenticate(session, authorization)
        project, member = guard_project(session, actor.id, project_id, exclusive=True)
        require_owner(member)
        result = MemberPublic.model_validate(add_member(session, project_id, payload.user_id))
    return result


@app.delete("/projects/{project_id}/members/{user_id}", status_code=204)
def uninvite(project_id: int = Path(gt=0, le=9223372036854775807),
             user_id: int = Path(gt=0, le=9223372036854775807),
             authorization: str | None = Header(default=None)):
    with SessionLocal.begin() as session:
        actor, credential = authenticate(session, authorization)
        project, member = guard_project(session, actor.id, project_id, exclusive=True)
        require_owner(member)
        remove_member(session, project_id, user_id)
    return Response(status_code=204)


@app.post("/projects/{project_id}/tasks", response_model=TaskPublic, status_code=201)
def new_task(payload: TaskInput, response: Response,
             project_id: int = Path(gt=0, le=9223372036854775807),
             authorization: str | None = Header(default=None),
             idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    with SessionLocal.begin() as session:
        actor, credential = authenticate(session, authorization)
        result, replayed = create_task_once(session, actor.id, project_id, payload,
                                            parse_key(idempotency_key), IDEMPOTENCY_TTL)
    response.headers["Idempotency-Replayed"] = "true" if replayed else "false"
    return result  # Normal response_model handling still runs; no raw JSONResponse bypass.


@app.get("/projects/{project_id}/tasks", response_model=TaskPage)
def task_list(project_id: int = Path(gt=0, le=9223372036854775807),
              limit: int = Query(default=20, ge=1, le=100), offset: int = Query(default=0, ge=0),
              authorization: str | None = Header(default=None)):
    with SessionLocal.begin() as session:
        actor, credential = authenticate(session, authorization)
        guard_project(session, actor.id, project_id)
        condition = Task.project_id == project_id
        records = session.scalars(select(Task).where(condition).order_by(Task.id).limit(limit).offset(offset)).all()
        result = {"items": [TaskPublic.model_validate(r) for r in records], "limit": limit,
                  "offset": offset, "total": session.scalar(select(func.count()).select_from(Task).where(condition))}
    return result


@app.get("/projects/{project_id}/tasks/{task_id}", response_model=TaskPublic)
def task_detail(project_id: int = Path(gt=0, le=9223372036854775807),
                task_id: int = Path(gt=0, le=9223372036854775807),
                authorization: str | None = Header(default=None)):
    with SessionLocal.begin() as session:
        actor, credential = authenticate(session, authorization)
        guard_project(session, actor.id, project_id)
        result = TaskPublic.model_validate(find_task(session, project_id, task_id))
    return result


@app.patch("/projects/{project_id}/tasks/{task_id}", response_model=TaskPublic)
def update_task(payload: TaskPatch, project_id: int = Path(gt=0, le=9223372036854775807),
                task_id: int = Path(gt=0, le=9223372036854775807),
                authorization: str | None = Header(default=None)):
    with SessionLocal.begin() as session:
        actor, credential = authenticate(session, authorization)
        project, member = guard_project(session, actor.id, project_id)
        record = find_task(session, project_id, task_id, write=True)
        may_edit_task(actor.id, member, record)
        result = TaskPublic.model_validate(patch_task(session, record, payload))
    return result


@app.delete("/projects/{project_id}/tasks/{task_id}", status_code=204)
def erase_task(project_id: int = Path(gt=0, le=9223372036854775807),
               task_id: int = Path(gt=0, le=9223372036854775807),
               authorization: str | None = Header(default=None)):
    with SessionLocal.begin() as session:
        actor, credential = authenticate(session, authorization)
        project, member = guard_project(session, actor.id, project_id)
        record = find_task(session, project_id, task_id, write=True)
        may_edit_task(actor.id, member, record)
        session.delete(record)
    return Response(status_code=204)
