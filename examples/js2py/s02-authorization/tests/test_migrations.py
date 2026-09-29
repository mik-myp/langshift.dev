import os
from pathlib import Path
import subprocess
import sys
import psycopg
from sqlalchemy import create_engine, text
from conftest import migrate


def test_existing_d_users_are_disabled_without_fake_hash_and_priority_survives(cluster):
    with psycopg.connect(host=str(cluster.socket_dir), port=cluster.port, user="lab_owner",
                         dbname="postgres", autocommit=True) as connection:
        connection.execute("CREATE DATABASE migration_history")
    url = cluster.url("migration_history")
    migrate(url, "001_base")
    engine = create_engine(url, hide_parameters=True)
    try:
        with engine.begin() as connection:
            uid = connection.scalar(text("INSERT INTO users(login) VALUES ('Legacy') RETURNING id"))
            pid = connection.scalar(text("INSERT INTO projects(name,created_by) VALUES ('Legacy project',:u) RETURNING id"), {"u":uid})
            connection.execute(text("INSERT INTO project_members VALUES (:p,:u,'owner')"), {"p":pid,"u":uid})
            connection.execute(text("INSERT INTO tasks(project_id,created_by,title) VALUES (:p,:u,'Historical task')"), {"p":pid,"u":uid})
        migrate(url, "003_contract")
        migrate(url)
        with engine.connect() as connection:
            user = connection.execute(text("SELECT password_hash,is_active,auth_version FROM users")).one()
            assert tuple(user) == (None, False, 1)
            assert connection.scalar(text("SELECT priority FROM tasks")) == 0
            assert connection.scalar(text("SELECT title FROM tasks")) == "Historical task"
        result = subprocess.run([sys.executable,"-m","alembic","downgrade","003_contract"],
            env=dict(os.environ,DATABASE_URL=url),capture_output=True,text=True,timeout=20)
        assert result.returncode != 0
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT title FROM tasks")) == "Historical task"
    finally:
        engine.dispose()


def test_multiple_legacy_owners_block_index_migration_without_silent_repair(cluster):
    with psycopg.connect(host=str(cluster.socket_dir), port=cluster.port, user="lab_owner",
                         dbname="postgres", autocommit=True) as connection:
        connection.execute("CREATE DATABASE owner_review")
    url = cluster.url("owner_review")
    migrate(url, "004_identity")
    engine = create_engine(url, hide_parameters=True)
    try:
        with engine.begin() as connection:
            alice = connection.scalar(text("INSERT INTO users(login) VALUES ('LegacyA') RETURNING id"))
            bob = connection.scalar(text("INSERT INTO users(login) VALUES ('LegacyB') RETURNING id"))
            pid = connection.scalar(text("INSERT INTO projects(name,created_by) VALUES ('Needs review',:a) RETURNING id"), {"a":alice})
            connection.execute(text("INSERT INTO project_members VALUES (:p,:a,'owner'),(:p,:b,'owner')"), {"p":pid,"a":alice,"b":bob})
        result = subprocess.run([sys.executable,"-m","alembic","upgrade","005_owner_guard"],
            env=dict(os.environ,DATABASE_URL=url),capture_output=True,text=True,timeout=20)
        assert result.returncode != 0
        with engine.begin() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "004_identity"
            assert connection.scalar(text("SELECT count(*) FROM project_members WHERE role='owner'")) == 2
            # Explicit reviewed decision for this disposable test dataset only.
            connection.execute(text("UPDATE project_members SET role='member' WHERE user_id=:b"), {"b":bob})
        migrate(url)
    finally:
        engine.dispose()
