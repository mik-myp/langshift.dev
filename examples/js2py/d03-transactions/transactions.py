"""Transaction owner is the caller, not the individual SQL helper."""
import labctl


def insert_project_and_owner(conn, name, creator_id, owner_id):
    project_id = conn.execute(
        "INSERT INTO projects(name, created_by) VALUES (%s, %s) RETURNING id",
        (name, creator_id),
    ).fetchone()[0]
    conn.execute(
        "INSERT INTO project_members(project_id, user_id, role) VALUES (%s, %s, %s)",
        (project_id, owner_id, "owner"),
    )
    return project_id


def create_project(name, creator_id):
    with labctl.connect() as conn:
        project_id = insert_project_and_owner(conn, name, creator_id, creator_id)
    # Context exit commits on success and closes. Commit itself may raise.
    # Only publish success AFTER that exit, not from inside the transaction.
    return project_id
