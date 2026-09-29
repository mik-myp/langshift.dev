def progress_report(conn, minimum_minutes=0):
    if type(minimum_minutes) is not int or minimum_minutes < 0:
        raise ValueError("minimum_minutes must be a nonnegative integer")
    return conn.execute("""
        SELECT p.name, count(t.id), coalesce(sum(t.minutes), 0)
        FROM projects AS p
        LEFT JOIN tasks AS t ON t.project_id=p.id AND t.status <> %s
        GROUP BY p.id, p.name
        HAVING coalesce(sum(t.minutes), 0) >= %s
        ORDER BY p.id
    """, ("done", minimum_minutes)).fetchall()
