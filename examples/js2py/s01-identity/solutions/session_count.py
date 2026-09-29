from fastapi import Header
from sqlalchemy import func, select
from app import app
from db import SessionLocal
from models import AuthSession
from security import authenticate, utc_now


@app.get("/users/me/session-count")
def session_count(authorization: str | None = Header(default=None)):
    with SessionLocal.begin() as session:
        actor, credential = authenticate(session, authorization)
        count = session.scalar(select(func.count()).select_from(AuthSession).where(
            AuthSession.user_id == actor.id, AuthSession.auth_version == actor.auth_version,
            AuthSession.revoked_at.is_(None), AuthSession.expires_at > utc_now()))
    return {"count": count}
