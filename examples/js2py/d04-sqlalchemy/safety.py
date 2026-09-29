"""Refuse arbitrary URLs. Only pg_sandbox's live, private cluster is accepted."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import uuid

import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url


NAME = re.compile(r"js2py_lab_[0-9a-f]{32}\Z")


def checked_url(value=None):
    value = value or os.environ.get("LAB_DATABASE_URL")
    root_value = os.environ.get("LAB_CLUSTER_ROOT")
    token = os.environ.get("LAB_CLUSTER_TOKEN")
    if not value or not root_value or not token:
        raise RuntimeError("Refusing database access: run inside python pg_sandbox.py -- COMMAND")
    root = Path(root_value).resolve()
    if root.parent != Path("/tmp").resolve() or not root.name.startswith("ls-pg-"):
        raise RuntimeError("Refusing non-sandbox cluster directory")
    marker = json.loads((root / "owner.json").read_text())
    url = make_url(value)
    if (marker["token"] != token or marker["root"] != str(root)
            or url.drivername != "postgresql+psycopg" or url.username != "lab_owner"
            or url.password is not None or url.host is not None or url.port is not None
            or not NAME.fullmatch(url.database or "")
            or dict(url.query) != {"host": str(root / "socket"), "port": "55432"}
            or not (root / "data" / "postmaster.pid").exists()):
        raise RuntimeError("Refusing a URL not owned by this sandbox")
    return url


def connect_admin(url):
    # CREATEDB for this disposable cluster only. Never a production credential.
    return psycopg.connect(dbname="postgres", user=url.username, host=url.query["host"],
                           port=int(url.query["port"]), autocommit=True)


@contextmanager
def fresh_database():
    base = checked_url()
    name = "js2py_lab_" + uuid.uuid4().hex
    with connect_admin(base) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {} OWNER lab_owner").format(sql.Identifier(name)))
    try:
        yield base.set(database=name).render_as_string(hide_password=False)
    finally:
        # No FORCE: an unreturned connection should make the test fail, not be hidden.
        with connect_admin(base) as admin:
            admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(name)))
