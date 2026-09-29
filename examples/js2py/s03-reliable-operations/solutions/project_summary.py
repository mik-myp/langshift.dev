from fastapi import Header, Path
from sqlalchemy import func, select
from app import app
from authorization import guard_project
from db import SessionLocal
from models import Task
from security import authenticate


@app.get("/projects/{project_id}/summary")
def summary(project_id: int = Path(gt=0, le=9223372036854775807),
            authorization: str | None = Header(default=None)):
    with SessionLocal.begin() as session:
        actor, credential = authenticate(session, authorization)
        guard_project(session, actor.id, project_id)
        count, minutes = session.execute(select(func.count(), func.coalesce(func.sum(Task.minutes), 0))
            .where(Task.project_id == project_id, Task.status != "done")).one()
    return {"count": count, "minutes": minutes}
