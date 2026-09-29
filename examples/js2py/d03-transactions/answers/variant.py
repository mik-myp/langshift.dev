def create_project_with_task(conn, name, creator_id, title):
    project_id = conn.execute(
        "INSERT INTO projects(name, created_by) VALUES (%s,%s) RETURNING id",
        (name, creator_id),
    ).fetchone()[0]
    conn.execute(
        "INSERT INTO project_members(project_id,user_id,role) VALUES (%s,%s,'owner')",
        (project_id, creator_id),
    )
    task_id = conn.execute(
        "INSERT INTO tasks(project_id,created_by,title) VALUES (%s,%s,%s) RETURNING id",
        (project_id, creator_id, title),
    ).fetchone()[0]
    return project_id, task_id
