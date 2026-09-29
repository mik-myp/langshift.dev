import psycopg
from ops.cluster import OwnedCluster,connect
from ops.data import grant_app,seed
from ops.migrate import upgrade
from ops.server import running


def drill():
    with OwnedCluster() as cluster:
        root=cluster.root
        upgrade(root,"006_task_operations")
        grant_app(root)
        tokens=seed(root)
        headers={"Authorization":"Bearer "+tokens["alice"]}
        with running(root,"v1") as client:
            assert client.get("/projects/1",headers=headers).json()=={"id":1,"name":"Alice project"}
            before=client.post("/projects",headers=headers,json={"name":"Before upgrade"})
            assert before.status_code==201
        print("PASS v1: real authenticated HTTP and committed baseline data")
        # A deliberate incompatible expansion fails transactionally, not by deleting data.
        try:
            with connect(root,"source") as conn:
                conn.execute("ALTER TABLE projects ADD COLUMN unsafe_required text NOT NULL")
        except psycopg.errors.NotNullViolation:
            pass
        else:raise AssertionError("Expected NOT NULL expansion to reject existing rows")
        with connect(root,"source") as conn:
            assert conn.execute("SELECT count(*) FROM projects").fetchone()[0]==3
            assert conn.execute("SELECT version_num FROM alembic_version").fetchone()[0]=="006_task_operations"
        print("PASS expected migration failure: old rows and revision preserved")
        upgrade(root,"007_project_description")
        with running(root,"v2") as client:
            created=client.post("/projects",headers=headers,json={"name":"After upgrade","description":"Preserve this value"})
            assert created.status_code==201
            project_id=created.json()["id"]
            assert client.get(f"/projects/{project_id}",headers=headers).json()["description"]=="Preserve this value"
        print("PASS v2: reviewed nullable expansion and new-data write")
        # Roll back application code, NOT the schema or the data volume.
        with running(root,"v1") as client:
            read=client.get(f"/projects/{project_id}",headers=headers)
            assert read.status_code==200 and "description" not in read.json()
            assert client.post("/projects",headers=headers,json={"name":"After app rollback"}).status_code==201
            assert client.get("/projects/2",headers=headers).status_code==404
        with connect(root,"source") as conn:
            assert conn.execute("SELECT description FROM projects WHERE id=%s",(project_id,)).fetchone()[0]=="Preserve this value"
            assert conn.execute("SELECT count(*) FROM projects").fetchone()[0]==5
            assert conn.execute("SELECT version_num FROM alembic_version").fetchone()[0]=="007_project_description"
        print("PASS rollback: v1 reads/writes expanded schema; v2 data retained; no downgrade")
    assert not root.exists()
    print("CLEANUP PASS: owned API processes and isolated PostgreSQL cluster removed")
