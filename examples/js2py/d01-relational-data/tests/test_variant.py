from pathlib import Path
import pytest
from psycopg import errors
import labctl


def test_comment_variation():
    with labctl.connect(autocommit=True) as conn:
        try:
            conn.execute((Path(__file__).parents[1] / "answers/variant.sql").read_text())
            assert conn.execute("SELECT count(*) FROM task_comments").fetchone() == (1,)
            with pytest.raises(errors.ForeignKeyViolation):
                conn.execute("INSERT INTO task_comments(task_id,author_id,body) VALUES(9999,1,'Hi')")
            with pytest.raises(errors.CheckViolation):
                conn.execute("INSERT INTO task_comments(task_id,author_id,body) VALUES(1,1,' ')")
        finally:
            conn.execute("DROP TABLE IF EXISTS task_comments")
