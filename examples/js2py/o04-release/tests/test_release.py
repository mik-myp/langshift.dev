import pytest
import psycopg
from ops.cluster import OwnedCluster,connect,checked_root
from ops.data import grant_app,seed
from ops.migrate import upgrade


def test_refuse_unowned_path():
    with pytest.raises(RuntimeError):checked_root("/tmp")


def test_migration_preserves_data_and_old_inserts():
    with OwnedCluster() as cluster:
        root=cluster.root
        upgrade(root,"006_task_operations");seed(root)
        upgrade(root,"007_project_description");grant_app(root)
        with connect(root,"source","lab_app") as conn:
            assert conn.execute("SELECT count(*) FROM tasks").fetchone()[0]==2
            value=conn.execute("INSERT INTO projects(name,created_by) VALUES ('Old app write',1) RETURNING description").fetchone()[0]
            assert value is None
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                with conn.transaction():conn.execute("ALTER TABLE projects ADD COLUMN forbidden int")


def test_duplicate_owner_rejected():
    with OwnedCluster() as cluster:
        upgrade(cluster.root,"006_task_operations");seed(cluster.root)
        with connect(cluster.root,"source") as conn:
            with pytest.raises(psycopg.errors.UniqueViolation):
                with conn.transaction():conn.execute("INSERT INTO project_members VALUES (1,2,'owner')")


def test_nonempty_target_cannot_be_created_again():
    with OwnedCluster() as cluster:
        with pytest.raises(RuntimeError):cluster.create_database("source")
