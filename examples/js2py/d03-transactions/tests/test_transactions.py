import pytest
from psycopg import IsolationLevel, errors
import labctl
import concurrency
from transactions import create_project, insert_project_and_owner
from answers.variant import create_project_with_task


def test_second_step_has_no_residue():
    assert concurrency.failed_second_step() == {"sqlstate": "23503", "projects_remaining": 0, "memberships": 4}


def test_commit_visibility_and_close():
    conn = labctl.connect()
    observer = labctl.connect(autocommit=True)
    try:
        project_id = insert_project_and_owner(conn, "Visible after commit", 1, 1)
        assert observer.execute("SELECT count(*) FROM projects WHERE id=%s", (project_id,)).fetchone() == (0,)
        conn.commit()
        assert observer.execute("SELECT count(*) FROM projects WHERE id=%s", (project_id,)).fetchone() == (1,)
        assert observer.execute("SELECT user_id,role FROM project_members WHERE project_id=%s", (project_id,)).fetchone() == (1, "owner")
    finally:
        conn.close()
        observer.close()
    assert conn.closed and observer.closed


def test_aborted_transaction_needs_rollback():
    with labctl.connect() as conn:
        conn.execute("UPDATE tasks SET minutes=35 WHERE id=1")
        with pytest.raises(errors.CheckViolation) as failure:
            conn.execute("UPDATE tasks SET minutes=-1 WHERE id=2")
        assert failure.value.sqlstate == "23514"
        with pytest.raises(errors.InFailedSqlTransaction) as aborted:
            conn.execute("SELECT 1")
        assert aborted.value.sqlstate == "25P02"
        conn.rollback()
        assert conn.execute("SELECT minutes FROM tasks WHERE id=1").fetchone() == (30,)
        assert conn.execute("SELECT 1").fetchone() == (1,)


def test_close_does_not_commit():
    conn = labctl.connect()
    conn.execute("UPDATE tasks SET minutes=999 WHERE id=1")
    conn.close()
    with labctl.connect(autocommit=True) as observer:
        assert observer.execute("SELECT minutes FROM tasks WHERE id=1").fetchone() == (30,)


def test_success_and_identity_gap():
    with labctl.connect() as conn:
        discarded = insert_project_and_owner(conn, "Discarded", 1, 1)
        conn.rollback()
    project_id = create_project("Committed", 1)
    assert project_id > discarded  # Identity allocation is not rolled back.


@pytest.mark.parametrize("level, expected", [
    (IsolationLevel.READ_COMMITTED, [30, 40]),
    (IsolationLevel.REPEATABLE_READ, [30, 30]),
])
def test_snapshot_boundary(level, expected):
    assert concurrency.snapshot(level) == expected


def test_actual_lost_update():
    assert concurrency.lost_update() == 37


def test_overlapping_atomic_updates_wait_then_add():
    assert concurrency.overlapping_write("increment") == {"lock_wait_observed": True, "worker": "committed", "value": 42}


def test_unique_constraint_arbitrates_two_connections():
    assert concurrency.overlapping_write("unique") == {"lock_wait_observed": True, "worker": "23505", "value": 1}


def test_row_lock_timeout_recovers():
    assert concurrency.lock_timeout() == {"sqlstate": "55P03", "minutes_after_rollback": 30}


def test_serialization_conflict_and_full_retry():
    assert concurrency.serialization_conflict() == {"sqlstate": "40001", "after_full_retry": 42}


def test_three_step_independent_variation():
    with pytest.raises(errors.CheckViolation):
        with labctl.connect() as conn:
            create_project_with_task(conn, "Three steps", 1, "   ")
    with labctl.connect(autocommit=True) as observer:
        assert observer.execute("SELECT count(*) FROM projects WHERE name='Three steps'").fetchone() == (0,)
        assert observer.execute("SELECT count(*) FROM project_members").fetchone() == (4,)
        assert observer.execute("SELECT count(*) FROM tasks").fetchone() == (5,)
    with labctl.connect() as conn:
        project_id, task_id = create_project_with_task(conn, "Three steps", 1, "First task")
    with labctl.connect(autocommit=True) as observer:
        assert observer.execute("SELECT project_id FROM tasks WHERE id=%s", (task_id,)).fetchone() == (project_id,)
        assert observer.execute(
            "SELECT name, created_by FROM projects WHERE id=%s", (project_id,),
        ).fetchone() == ("Three steps", 1)
        assert observer.execute(
            "SELECT user_id, role FROM project_members WHERE project_id=%s ORDER BY user_id",
            (project_id,),
        ).fetchall() == [(1, "owner")]
        assert observer.execute(
            "SELECT project_id, created_by, title FROM tasks WHERE id=%s", (task_id,),
        ).fetchone() == (project_id, 1, "First task")
