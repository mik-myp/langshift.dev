"""Business operations borrow a Session; only the caller owns commit/rollback."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from models import Project, ProjectMember, Task, User


def seed_user(session: Session, login="alice") -> int:
    user = User(login=login)
    session.add(user)
    session.flush()
    return user.id


def create_project(session: Session, name: str, owner_id: int, *, owner_role="owner") -> dict:
    project = Project(name=name, created_by=owner_id)
    session.add(project)
    session.flush()  # INSERT obtains identity; this is NOT a durable commit.
    session.add(ProjectMember(project_id=project.id, user_id=owner_id, role=owner_role))
    session.flush()  # Second write may fail: both belong to caller's transaction.
    return {"id": project.id, "name": project.name, "created_by": project.created_by}


def create_task(session: Session, project_id: int, *, title: str, created_by: int,
                minutes: int = 0, status: str = "todo", description: str | None = None) -> dict:
    task = Task(project_id=project_id, title=title, created_by=created_by,
                minutes=minutes, status=status, description=description)
    session.add(task)
    session.flush()
    return task_dto(task)


def task_dto(task: Task) -> dict:
    return {"id": task.id, "project_id": task.project_id, "created_by": task.created_by,
            "title": task.title, "description": task.description,
            "minutes": task.minutes, "status": task.status}


def list_tasks(session: Session, project_id: int, status=None, limit=20, offset=0):
    query = select(Task).where(Task.project_id == project_id)
    if status is not None:
        query = query.where(Task.status == status)
    query = query.order_by(Task.id).limit(limit).offset(offset)
    return [task_dto(task) for task in session.scalars(query)]
