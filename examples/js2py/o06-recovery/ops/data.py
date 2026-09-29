import hashlib
from pathlib import Path
import secrets
from argon2 import PasswordHasher
from psycopg import sql

from ops.cluster import connect


def grant_app(root, database="source"):
    with connect(root, database) as conn:
        conn.execute((Path(__file__).resolve().parents[1] / "sql/grants.sql").read_text())
        conn.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO lab_app").format(sql.Identifier(database)))


def issue_fixture_token(root, user_id, database="source", expired=False):
    # Operator-only synthetic test data; NOT a replacement public login endpoint.
    token = secrets.token_urlsafe(32)
    digest = hashlib.sha256(token.encode("ascii")).hexdigest()
    with connect(root, database) as conn:
        conn.execute("""INSERT INTO auth_sessions(token_digest,user_id,auth_version,issued_at,expires_at)
            SELECT %s,id,auth_version,now()-interval '2 hours',
                   now() + CASE WHEN %s THEN interval '-1 hour' ELSE interval '15 minutes' END
            FROM users WHERE id=%s""", (digest, expired, user_id))
    return token


def seed(root):
    password_hash = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4).hash(secrets.token_urlsafe(24))
    with connect(root, "source") as conn:
        for name in ["Alice", "Bob"]:
            user_id = conn.execute("INSERT INTO users(login,password_hash,is_active) VALUES (%s,%s,true) RETURNING id", (name,password_hash)).fetchone()[0]
            project_id = conn.execute("INSERT INTO projects(name,created_by) VALUES (%s,%s) RETURNING id", (name+" project",user_id)).fetchone()[0]
            conn.execute("INSERT INTO project_members(project_id,user_id,role) VALUES (%s,%s,'owner')", (project_id,user_id))
            conn.execute("INSERT INTO tasks(project_id,created_by,title,minutes) VALUES (%s,%s,%s,30)", (project_id,user_id,name+" task"))
    with connect(root,"source") as conn:
        # Nonempty synthetic idempotency receipt: backup coverage must not skip it.
        conn.execute("""INSERT INTO task_operations(actor_id,project_id,operation,key,request_digest,response_body,response_status,created_at,expires_at)
            SELECT 1,1,'create-task-v1',gen_random_uuid(),%s,to_jsonb(t),201,now(),now()+interval '1 day'
            FROM tasks t WHERE t.id=1""", (hashlib.sha256(b"synthetic fixture request").hexdigest(),))
    return {"alice": issue_fixture_token(root,1), "bob": issue_fixture_token(root,2)}
