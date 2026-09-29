import hashlib
import json
from pathlib import Path
import time
from psycopg import sql

from ops.cluster import connect

TABLES=("users","projects","project_members","tasks","auth_sessions","task_operations","alembic_version")


def fingerprint(root,database):
    result={}
    with connect(root,database) as conn:
        for table in TABLES:
            rows=conn.execute(sql.SQL("SELECT to_jsonb(t) FROM {} t").format(sql.Identifier(table))).fetchall()
            encoded=sorted(json.dumps(row[0],sort_keys=True,default=str) for row in rows)
            result[table]={"count":len(rows),"sha256":hashlib.sha256("\n".join(encoded).encode()).hexdigest()}
    return result


def backup(cluster):
    folder=cluster.root/"backups";folder.mkdir(mode=0o700)
    archive=folder/"snapshot.dump"
    # Deterministic lab boundary: no concurrent writers during this snapshot/check.
    expected=fingerprint(cluster.root,"source")
    started=time.time()
    cluster.run("pg_dump","-h",cluster.root/"socket","-p","5432","-U","lab_owner","-d","source","--format=custom","--no-owner","--no-privileges","--file",archive)
    archive.chmod(0o600)
    manifest={"created_at":started,"postgres":"18.6","tables":expected,
              "sha256":hashlib.sha256(archive.read_bytes()).hexdigest(),"bytes":archive.stat().st_size}
    path=folder/"manifest.json";path.write_text(json.dumps(manifest,sort_keys=True,indent=2));path.chmod(0o600)
    assert manifest["bytes"]>0
    # A successful listing is only an inventory check, NOT restore acceptance.
    cluster.run("pg_restore","--list",archive)
    return archive,manifest


def restore(cluster,archive:Path,manifest:dict,target="restored"):
    if archive.parent != cluster.root/"backups" or archive.is_symlink():
        raise RuntimeError("Only this run's private archive may be restored")
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=manifest["sha256"]:
        raise ValueError("Archive checksum mismatch; stop before creating the target")
    cluster.create_database(target)  # Refuses existing/non-allowlisted targets.
    cluster.run("pg_restore","-h",cluster.root/"socket","-p","5432","-U","lab_owner","-d",target,
                "--no-owner","--no-privileges","--exit-on-error","--single-transaction",archive)
    if fingerprint(cluster.root,target)!=manifest["tables"]:
        raise AssertionError("Restored row counts/content differ; keep target isolated")


def quarantine_sessions(root,database):
    with connect(root,database) as conn:
        # A backup can revive a revoked session or account. Fail closed before grants.
        conn.execute("UPDATE users SET is_active=false,auth_version=auth_version+1")
        conn.execute("DELETE FROM auth_sessions")


def approve_fixture_accounts(root,database):
    # In a real recovery, reconcile post-backup security changes from a trusted
    # separate record before approving users. This is the known synthetic ledger.
    with connect(root,database) as conn:
        conn.execute("DELETE FROM project_members WHERE project_id=1 AND user_id=2 AND role='member'")
        conn.execute("UPDATE users SET is_active=true WHERE id IN (1,2)")
