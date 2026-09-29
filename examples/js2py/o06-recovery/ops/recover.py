import hashlib
import json
import stat
import time
import psycopg

from ops.backup import backup,restore,quarantine_sessions,approve_fixture_accounts
from ops.cluster import OwnedCluster,connect
from ops.data import seed,grant_app,issue_fixture_token
from ops.migrate import upgrade
from ops.server import running


def constraint_checks(root,database):
    with connect(root,database) as conn:
        for statement,error in [
            ("INSERT INTO users(login) VALUES ('Alice')",psycopg.errors.UniqueViolation),
            ("INSERT INTO tasks(project_id,created_by,title,minutes) VALUES (9999,1,'No project',0)",psycopg.errors.ForeignKeyViolation),
            ("INSERT INTO tasks(project_id,created_by,title,minutes) VALUES (1,1,'Bad minutes',-1)",psycopg.errors.CheckViolation),
            ("INSERT INTO project_members VALUES(2,1,'owner')",psycopg.errors.UniqueViolation),
            ("INSERT INTO auth_sessions(token_digest,user_id,auth_version,issued_at,expires_at) VALUES ('bad',1,1,now(),now()+interval '1 hour')",psycopg.errors.CheckViolation),
            ("INSERT INTO auth_sessions(token_digest,user_id,auth_version,issued_at,expires_at) VALUES (repeat('a',64),1,1,now(),now()-interval '1 hour')",psycopg.errors.CheckViolation),
            ("INSERT INTO task_operations SELECT * FROM task_operations LIMIT 1",psycopg.errors.UniqueViolation),
        ]:
            try:
                with conn.transaction():conn.execute(statement)
            except error as caught:
                if "project_members" in statement:
                    # Use a distinct membership pair: prove the partial owner index,
                    # not an unrelated duplicate (project_id, user_id) primary key.
                    assert caught.diag.constraint_name=="project_members_one_owner"
            else:raise AssertionError("Restored constraint failed to reject invalid data")
        assert conn.execute("SELECT count(*) FROM tasks").fetchone()[0]==2


def drill():
    with OwnedCluster() as cluster:
        root=cluster.root
        upgrade(root,"007_project_description");grant_app(root);old_tokens=seed(root)
        with connect(root,"source") as conn:
            conn.execute("INSERT INTO project_members VALUES(1,2,'member')")
            conn.execute("UPDATE projects SET description='Snapshot value' WHERE id=1")
        archive,manifest=backup(cluster)
        assert stat.S_IMODE(archive.stat().st_mode)==0o600
        print("PASS backup: custom archive and inventory created privately; restore still required")
        # Known post-backup writes and security changes are NOT in the snapshot.
        with connect(root,"source") as conn:
            conn.execute("INSERT INTO tasks(project_id,created_by,title) VALUES(1,1,'After snapshot')")
            conn.execute("UPDATE users SET auth_version=auth_version+1 WHERE id=1")
            conn.execute("DELETE FROM project_members WHERE project_id=1 AND user_id=2")
        broken=root/"backups/broken.dump";broken.write_bytes(archive.read_bytes()[:64]);broken.chmod(0o600)
        try:restore(cluster,broken,manifest,target="damaged")
        except ValueError:pass
        else:raise AssertionError("Corrupt archive must fail checksum gate")
        # Also exercise pg_restore itself, not just our checksum guard.
        cluster.create_database("damaged")
        failed=cluster.run("pg_restore","-h",root/"socket","-U","lab_owner","-d","damaged","--exit-on-error","--single-transaction",broken,check=False)
        assert failed.returncode!=0
        with connect(root,"damaged") as conn:
            assert conn.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'").fetchone()[0]==0
        started=time.perf_counter()
        restore(cluster,archive,manifest)
        print("PASS restore: actual pg_restore, all table fingerprints match; corrupt restore rejected")
        constraint_checks(root,"restored")
        with connect(root,"restored") as conn:
            # Observe why restoring auth tables alone is unsafe, while still isolated.
            digest=hashlib.sha256(old_tokens["alice"].encode("ascii")).hexdigest()
            assert conn.execute("SELECT count(*) FROM auth_sessions s JOIN users u ON u.id=s.user_id WHERE s.token_digest=%s AND s.auth_version=u.auth_version AND s.revoked_at IS NULL AND s.expires_at>now() AND u.is_active",(digest,)).fetchone()[0]==1
            assert not conn.execute("SELECT has_database_privilege('lab_app','restored','CONNECT')").fetchone()[0]
        quarantine_sessions(root,"restored")
        with connect(root,"restored") as conn:
            assert conn.execute("SELECT count(*) FROM users WHERE is_active").fetchone()[0]==0
        approve_fixture_accounts(root,"restored")
        grant_app(root,"restored")
        new_tokens={"alice":issue_fixture_token(root,1,"restored"),"bob":issue_fixture_token(root,2,"restored")}
        expired=issue_fixture_token(root,1,"restored",expired=True)
        with running(root,"v2","restored") as client:
            for token in [old_tokens["alice"],old_tokens["bob"],expired,"invalid"]:
                assert client.get("/projects/1",headers={"Authorization":"Bearer "+token}).status_code==401
            alice={"Authorization":"Bearer "+new_tokens["alice"]};bob={"Authorization":"Bearer "+new_tokens["bob"]}
            assert client.get("/projects/1",headers=alice).json()["description"]=="Snapshot value"
            assert client.get("/projects/2",headers=alice).status_code==404
            assert client.get("/projects/1",headers=bob).status_code==404
            assert client.get("/projects/2",headers=bob).status_code==200
            created=client.post("/projects",headers=alice,json={"name":"Restored sequence"})
            assert created.status_code==201 and created.json()["id"]>2
        with connect(root,"restored","lab_app") as conn:
            try:
                with conn.transaction():conn.execute("DROP TABLE tasks")
            except psycopg.errors.InsufficientPrivilege:pass
            else:raise AssertionError("Runtime role must not own restored tables")
            assert conn.execute("SELECT count(*) FROM tasks").fetchone()[0]==2
        elapsed=time.perf_counter()-started
        with connect(root,"source") as conn:assert conn.execute("SELECT count(*) FROM tasks").fetchone()[0]==3
        for path in root.glob("*.log"):
            text=path.read_text()
            assert all(token not in text for token in [*old_tokens.values(),*new_tokens.values(),expired])
        print("PASS security: stale/expired tokens denied; reviewed memberships; cross-user 404; app cannot DROP")
        print("MEASURED",json.dumps({"restore_and_validation_seconds":round(elapsed,3),"known_post_snapshot_rows_not_recovered":1,"snapshot_age_seconds":round(time.time()-manifest["created_at"],3),"scope":"synthetic local drill, not promised production RPO/RTO"},sort_keys=True))
    assert not root.exists()
    print("CLEANUP PASS: source/targets/archive/private logs and owned processes removed")
