import labctl
from queries import create_task, delete_task, find_by_title, list_tasks, project_totals, update_status


with labctl.connect(autocommit=True) as conn:
    print("todo", list_tasks(conn, status="todo"))
    print("page", list_tasks(conn, limit=2, offset=2))
    print("totals", project_totals(conn))
    payload = "x' OR TRUE --"
    print("unmatched payload", find_by_title(conn, payload))
    created = create_task(conn, payload)
    print("literal stored", find_by_title(conn, payload))
    print("updated", update_status(conn, created[0], "doing"))
    print("deleted", delete_task(conn, created[0]))
    print("tasks remaining", conn.execute("SELECT count(*) FROM tasks").fetchone()[0])
