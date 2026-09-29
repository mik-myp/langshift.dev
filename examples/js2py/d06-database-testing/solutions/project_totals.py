"""Keep empty projects; a WHERE task.status filter would erase them."""
from sqlalchemy import and_, func, select
from models import Project, Task


def done_minutes(session, project_ids):
    statement = (
        select(Project.id, func.coalesce(func.sum(Task.minutes), 0).label("minutes"))
        .outerjoin(Task, and_(Task.project_id == Project.id, Task.status == "done"))
        .where(Project.id.in_(project_ids))
        .group_by(Project.id)
        .order_by(Project.id)
    )
    return {row.id: row.minutes for row in session.execute(statement)}
