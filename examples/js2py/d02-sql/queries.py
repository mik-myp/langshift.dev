"""Statement helpers: caller owns the connection and transaction boundary."""
from psycopg import Connection

ORDERINGS = {"id": "t.id ASC", "minutes": "t.minutes DESC, t.id ASC"}
STATUSES = {"todo", "doing", "done"}


def list_tasks(conn: Connection, *, status=None, limit=20, offset=0, sort="id"):
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer from 1 to 100")
    if type(offset) is not int or offset < 0:
        raise ValueError("offset must be a nonnegative integer")
    if status is not None and status not in STATUSES:
        raise ValueError("unknown status")
    if sort not in ORDERINGS:
        raise ValueError("unknown sort")
    statement = "SELECT t.id, t.title, t.status, t.minutes FROM tasks AS t"
    params = []
    if status is not None:
        statement += " WHERE t.status = %s"
        params.append(status)
    # Only our constant fragments enter the SQL grammar, never the raw sort input.
    statement += " ORDER BY " + ORDERINGS[sort] + " LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    with conn.cursor() as cursor:
        cursor.execute(statement, params)
        return cursor.fetchall()


def find_by_title(conn: Connection, title: str):
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, title FROM tasks WHERE title = %s ORDER BY id", (title,))
        return cursor.fetchall()


def create_task(conn: Connection, title: str, *, project_id=1, created_by=1):
    if not isinstance(title, str) or not title.strip() or len(title) > 120:
        raise ValueError("title must contain 1..120 characters, not only whitespace")
    return conn.execute(
        "INSERT INTO tasks (project_id, created_by, title) VALUES (%s, %s, %s) "
        "RETURNING id, title, status", (project_id, created_by, title)
    ).fetchone()


def update_status(conn: Connection, task_id: int, status: str):
    if status not in STATUSES:
        raise ValueError("unknown status")
    return conn.execute(
        "UPDATE tasks SET status=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s "
        "RETURNING id, status", (status, task_id)
    ).fetchone()


def delete_task(conn: Connection, task_id: int):
    return conn.execute("DELETE FROM tasks WHERE id=%s RETURNING id", (task_id,)).fetchone()


def project_totals(conn: Connection):
    return conn.execute("""
        SELECT p.name, count(t.id), coalesce(sum(t.minutes), 0)
        FROM projects AS p LEFT JOIN tasks AS t ON t.project_id=p.id
        GROUP BY p.id, p.name ORDER BY p.id
    """).fetchall()
