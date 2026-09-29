from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from api import create_app
from db import make_engine, session_factory
from models import Base, Project, ProjectMember
from services import create_project, seed_user


def main():
    engine = make_engine()
    try:
        Base.metadata.create_all(engine)
        sessions = session_factory(engine)
        with sessions.begin() as session:
            owner = seed_user(session)
        try:
            with sessions.begin() as session:
                create_project(session, "must disappear", owner, owner_role="broken")
        except IntegrityError:
            print("second write rejected; transaction rolled back")
        with sessions() as session:
            print("projects after failure:", session.scalar(select(func.count()).select_from(Project)))
            print("members after failure:", session.scalar(select(func.count()).select_from(ProjectMember)))
        with TestClient(create_app(engine)) as client:
            response = client.post("/projects", json={"name": "Study", "owner_id": owner})
            print("API status:", response.status_code)
            print("API projects:", [p["name"] for p in client.get("/projects").json()])
            print("checked out:", engine.pool.checkedout())
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
