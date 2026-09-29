import pytest
from psycopg import errors
import labctl
from queries import create_task, delete_task, find_by_title, list_tasks, project_totals, update_status
from answers.variant import progress_report


def test_filter_order_page_and_aggregate():
    with labctl.connect(autocommit=True) as conn:
        assert [r[0] for r in list_tasks(conn, status="todo")] == [1, 4]
        assert [r[0] for r in list_tasks(conn, limit=2, offset=2)] == [3, 4]
        assert [r[0] for r in list_tasks(conn, sort="minutes", limit=2)] == [2, 5]
        assert project_totals(conn) == [("Launch", 3, 90), ("Docs", 2, 60), ("Empty", 0, 0)]
        assert progress_report(conn) == [("Launch", 2, 75), ("Docs", 1, 20), ("Empty", 0, 0)]
        assert progress_report(conn, 30) == [("Launch", 2, 75)]


@pytest.mark.parametrize("options", [
    {"limit": 0}, {"limit": 101}, {"limit": True}, {"limit": "2"},
    {"offset": -1}, {"offset": False}, {"status": "later"},
    {"sort": "id; DROP TABLE tasks; --"},
])
def test_reject_bad_query_options(options):
    with labctl.connect(autocommit=True) as conn:
        with pytest.raises(ValueError):
            list_tasks(conn, **options)
        assert conn.execute("SELECT count(*) FROM tasks").fetchone() == (5,)


@pytest.mark.parametrize("payload", ["x' OR TRUE --", "'; DROP TABLE tasks; --"])
def test_payload_stays_a_value(payload):
    with labctl.connect(autocommit=True) as conn:
        assert find_by_title(conn, payload) == []
        row = create_task(conn, payload)
        assert find_by_title(conn, payload) == [(row[0], payload)]
        assert conn.execute("SELECT count(*) FROM tasks").fetchone() == (6,)
        assert delete_task(conn, row[0]) == (row[0],)
        assert conn.execute("SELECT count(*) FROM tasks").fetchone() == (5,)


def test_update_delete_missing_and_constraints():
    with labctl.connect(autocommit=True) as conn:
        assert update_status(conn, 1, "done") == (1, "done")
        assert update_status(conn, 9999, "done") is None
        assert delete_task(conn, 9999) is None
        assert delete_task(conn, 5) == (5,)
        with pytest.raises(errors.ForeignKeyViolation):
            create_task(conn, "Orphan", project_id=9999)


def test_null_and_left_join_trap():
    with labctl.connect(autocommit=True) as conn:
        assert conn.execute("SELECT NULL = NULL, NULL IS NULL").fetchone() == (None, True)
        assert conn.execute("SELECT count(*) FROM tasks WHERE description = NULL").fetchone() == (0,)
        assert conn.execute("SELECT count(*) FROM tasks WHERE description IS NULL").fetchone() == (2,)
        assert conn.execute("SELECT count(*), count(t.id) FROM projects p LEFT JOIN tasks t "
                            "ON t.project_id=p.id WHERE p.name='Empty'").fetchone() == (1, 0)
        assert conn.execute("SELECT p.name FROM projects p LEFT JOIN tasks t ON t.project_id=p.id "
                            "WHERE t.status='todo' ORDER BY p.id").fetchall() == [("Launch",), ("Docs",)]


def test_join_multiplication_and_distinct():
    with labctl.connect(autocommit=True) as conn:
        assert conn.execute("SELECT count(t.id), count(DISTINCT t.id) FROM tasks t "
                            "JOIN project_members m ON m.project_id=t.project_id "
                            "WHERE t.project_id=1").fetchone() == (6, 3)


def test_parameter_is_not_identifier():
    with labctl.connect(autocommit=True) as conn:
        assert conn.execute("SELECT %s FROM tasks WHERE id=1", ("title",)).fetchone() == ("title",)


def test_offset_is_not_a_snapshot_across_requests():
    with labctl.connect(autocommit=True) as conn:
        assert [r[0] for r in list_tasks(conn, limit=2)] == [1, 2]
        delete_task(conn, 1)
        assert [r[0] for r in list_tasks(conn, limit=2, offset=2)] == [4, 5]
        # id=3 was not returned: stable ordering does not freeze changing data.
