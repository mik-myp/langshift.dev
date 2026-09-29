import pytest
from psycopg import errors
import labctl


def test_identity_relations_and_types():
    with labctl.connect(autocommit=True) as conn:
        assert conn.info.server_version == 180006
        assert conn.execute("SELECT count(*) FROM tasks").fetchone() == (5,)
        assert conn.execute("SELECT count(*) FROM project_members").fetchone() == (4,)
        columns = dict(conn.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name='tasks' AND table_schema='public'"
        ).fetchall())
        assert columns["id"] == "bigint"
        assert columns["due_at"] == "timestamp with time zone"
        assert conn.execute("SELECT rolsuper FROM pg_roles WHERE rolname=current_user").fetchone() == (False,)


@pytest.mark.parametrize("sql, error, state", [
    ("INSERT INTO users(login) VALUES ('alice')", errors.UniqueViolation, "23505"),
    ("INSERT INTO project_members VALUES (1,1,'member')", errors.UniqueViolation, "23505"),
    ("INSERT INTO project_members VALUES (1,9999,'member')", errors.ForeignKeyViolation, "23503"),
    ("INSERT INTO project_members VALUES (1,2,'boss')", errors.CheckViolation, "23514"),
    ("UPDATE tasks SET title=NULL WHERE id=1", errors.NotNullViolation, "23502"),
    ("UPDATE tasks SET title='   ' WHERE id=1", errors.CheckViolation, "23514"),
    ("UPDATE tasks SET title=repeat('x',121) WHERE id=1", errors.StringDataRightTruncation, "22001"),
    ("UPDATE tasks SET status='later' WHERE id=1", errors.CheckViolation, "23514"),
    ("UPDATE tasks SET minutes=-1 WHERE id=1", errors.CheckViolation, "23514"),
    ("UPDATE tasks SET minutes=NULL WHERE id=1", errors.NotNullViolation, "23502"),
    ("DELETE FROM projects WHERE id=1", errors.RestrictViolation, "23001"),
])
def test_database_rejects_bad_rows(sql, error, state):
    with labctl.connect(autocommit=True) as conn:
        with pytest.raises(error) as captured:
            conn.execute(sql)
        assert captured.value.sqlstate == state
        assert conn.execute("SELECT title, minutes FROM tasks WHERE id=1").fetchone() == ("Design API", 30)
        assert conn.execute("SELECT count(*) FROM tasks").fetchone() == (5,)


def test_null_is_not_empty_string_and_check_is_not_not_null():
    with labctl.connect(autocommit=True) as conn:
        assert conn.execute("SELECT id FROM tasks WHERE description IS NULL ORDER BY id").fetchall() == [(1,), (4,)]
        assert conn.execute("SELECT id FROM tasks WHERE description='' ORDER BY id").fetchall() == [(2,)]
        conn.execute("CREATE TEMP TABLE check_only (minutes integer CHECK (minutes >= 0))")
        conn.execute("INSERT INTO check_only VALUES (NULL)")
        assert conn.execute("SELECT minutes FROM check_only").fetchone() == (None,)
