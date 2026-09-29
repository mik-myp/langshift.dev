"""Revision-aware SQL: do not query a final ORM column before its migration."""
from sqlalchemy import text


def insert_old_task(connection, title="Original", *, user_id=None, project_id=None):
    if user_id is None:
        user_id = connection.execute(text("INSERT INTO users(login) VALUES ('alice') RETURNING id")).scalar_one()
        project_id = connection.execute(text("INSERT INTO projects(name, created_by) VALUES ('Study', :u) RETURNING id"), {"u": user_id}).scalar_one()
        connection.execute(text("INSERT INTO project_members VALUES (:p, :u, 'owner')"), {"p": project_id, "u": user_id})
    task_id = connection.execute(text("""
        INSERT INTO tasks(project_id, created_by, title, description, minutes, status)
        VALUES (:p, :u, :t, 'keep this note', 30, 'done') RETURNING id
    """), {"p": project_id, "u": user_id, "t": title}).scalar_one()
    return user_id, project_id, task_id


def snapshot(connection):
    return connection.execute(text("""
        SELECT id, project_id, created_by, title, description, status, minutes,
               due_at, created_at, updated_at FROM tasks ORDER BY id
    """)).mappings().all()
