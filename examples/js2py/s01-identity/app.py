from fastapi import FastAPI, Header, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from db import SessionLocal, SESSION_TTL, EXPECTED_REVISION
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
