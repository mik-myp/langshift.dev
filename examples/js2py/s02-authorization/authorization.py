"""DB-backed object policy. Helpers flush/return; the endpoint owns commit."""
from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from models import Project, ProjectMember, Task, User
from schemas import TaskInput, TaskPatch
from security import utc_now


def guard_project(session: Session, actor_id: int, project_id: int, *, exclusive=False):
    # Membership mutations take this same row EXCLUSIVELY. Holding a shared lock
    # through commit orders ordinary requests before/after membership removal.
    project = session.scalar(select(Project).where(Project.id == project_id)
                             .with_for_update(read=not exclusive))
    if project is None:
        raise HTTPException(404, "Project not found")
    member = session.get(ProjectMember, (project_id, actor_id))
    if member is None:
        raise HTTPException(404, "Project not found")
    return project, member


def require_owner(member: ProjectMember):
    if member.role != "owner":
        raise HTTPException(403, "Project owner required")


def create_project(session: Session, actor_id: int, name: str):
    project = Project(name=name, created_by=actor_id)
    session.add(project)
    session.flush()  # Get the DB id; NOT a commit.
    session.add(ProjectMember(project_id=project.id, user_id=actor_id, role="owner"))
    session.flush()
    return project


def add_member(session: Session, project_id: int, target_id: int):
    target = session.get(User, target_id)
    if target is None or not target.is_active:
        raise HTTPException(404, "Invitee unavailable")
    member = ProjectMember(project_id=project_id, user_id=target_id, role="member")
    session.add(member)
    session.flush()  # PK conflict is the final concurrent duplicate guard.
    return member


def remove_member(session: Session, project_id: int, target_id: int):
    target = session.get(ProjectMember, (project_id, target_id))
    if target is None:
        raise HTTPException(404, "Member not found")
    if target.role == "owner":
        raise HTTPException(409, "Cannot remove the project owner")
    session.delete(target)
    session.flush()


def create_task(session: Session, actor_id: int, project_id: int, payload: TaskInput):
    record = Task(project_id=project_id, created_by=actor_id, **payload.model_dump())
    session.add(record)
    session.flush()
    return record


def find_task(session: Session, project_id: int, task_id: int, *, write=False):
    statement = select(Task).where(Task.id == task_id, Task.project_id == project_id)
    if write:
        statement = statement.with_for_update()
    record = session.scalar(statement)
    if record is None:
        raise HTTPException(404, "Task not found")
    return record


def may_edit_task(actor_id: int, member: ProjectMember, task: Task):
    if member.role != "owner" and task.created_by != actor_id:
        raise HTTPException(403, "Task creator or project owner required")


def patch_task(session: Session, record: Task, payload: TaskPatch):
    candidate = {field: getattr(record, field) for field in TaskInput.model_fields}
    changes = payload.model_dump(exclude_unset=True)
    candidate.update(changes)
    TaskInput.model_validate(candidate)
    if changes:
        for name, value in changes.items():
            setattr(record, name, value)
        record.updated_at = utc_now()
    session.flush()
    return record


def delete_project(session: Session, project: Project):
    # The caller holds the exclusive project lock and has checked ownership.
    # FK RESTRICT remains intact: children are explicitly removed in order.
    session.execute(delete(Task).where(Task.project_id == project.id))
    session.execute(delete(ProjectMember).where(ProjectMember.project_id == project.id))
    session.delete(project)
    session.flush()
