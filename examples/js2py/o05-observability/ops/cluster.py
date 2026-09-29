"""Only creates/controls our own mkdtemp PostgreSQL 18.6 cluster. No DSN input."""
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import uuid

import psycopg
from psycopg import sql


def pg_bin(name: str) -> str:
    directory = os.environ.get("PG_BIN", "/opt/homebrew/bin")
    path = Path(directory) / name
    if not path.is_file():
        found = shutil.which(name)
        if not found:
            raise RuntimeError(f"Install PostgreSQL 18.6 tools first: missing {name}")
        path = Path(found)
    result = subprocess.run([str(path), "--version"], capture_output=True, text=True, check=True)
    if " 18.6" not in result.stdout:
        raise RuntimeError("This acceptance requires PostgreSQL 18.6 client/server tools")
    return str(path)


def reject_connection_environment():
    """Fail closed before libpq can read inherited connection defaults.

    This check does not mutate the caller's environment (including in threads).
    PG_BIN is our executable locator, not a libpq connection parameter.
    Report names only: values may contain credentials or private paths.
    """
    names = sorted(name for name in os.environ if name.startswith("PG") and name != "PG_BIN")
    if names:
        raise RuntimeError(
            "Refusing inherited PostgreSQL environment; unset these names for this lab: "
            + ", ".join(names)
        )


def checked_root(value: str) -> Path:
    root = Path(value)
    if root.is_symlink() or root.resolve().parent != Path("/tmp").resolve() or not root.name.startswith("ls-ops-"):
        raise RuntimeError("Refusing a non-owned laboratory directory")
    if root.stat().st_uid != os.getuid() or stat.S_IMODE(root.stat().st_mode) != 0o700:
        raise RuntimeError("Laboratory directory must be owned by this user and mode 0700")
    marker = json.loads((root / "owner.json").read_text())
    if marker.get("kind") != "langshift-owned-pg18.6" or marker.get("uid") != os.getuid():
        raise RuntimeError("Invalid laboratory ownership marker")
    if (root / "socket").is_symlink() or (root / "data").is_symlink():
        raise RuntimeError("Refusing symlinked cluster paths")
    passfile = root / "empty.pgpass"
    if (passfile.is_symlink() or not passfile.is_file() or passfile.stat().st_size != 0
            or passfile.stat().st_uid != os.getuid()
            or stat.S_IMODE(passfile.stat().st_mode) != 0o600):
        raise RuntimeError("Expected this lab's private empty password file")
    return root


def connect(root: Path, database: str, user: str = "lab_owner"):
    reject_connection_environment()
    checked_root(str(root))
    if database not in {"postgres", "source", "restored", "damaged"} or user not in {"lab_owner", "lab_app"}:
        raise RuntimeError("Database/role is outside this laboratory allowlist")
    return psycopg.connect(host=str(root / "socket"), port=5432, dbname=database,
                          user=user, connect_timeout=3, passfile=str(root / "empty.pgpass"),
                          options="-c statement_timeout=5000 -c lock_timeout=1000")


class OwnedCluster:
    def __init__(self):
        self.root = None
        self.nonce = uuid.uuid4().hex
        self.started = False
        self.databases = set()

    def run(self, executable: str, *arguments: str, check=True):
        env = {key: value for key, value in os.environ.items() if not key.startswith("PG")}
        env["PGPASSFILE"] = str(self.root / "empty.pgpass")  # Never consult the user's ~/.pgpass.
        result = subprocess.run([pg_bin(executable), *map(str, arguments)],
                                env=env, text=True, capture_output=True, timeout=45, umask=0o077)
        if check and result.returncode:
            # Do not print arbitrary database diagnostics/SQL values or connection strings.
            raise RuntimeError(f"{executable} failed (exit {result.returncode}); inspect private lab diagnostics")
        return result

    def __enter__(self):
        reject_connection_environment()  # Before creating even a temporary directory.
        self.root = Path(tempfile.mkdtemp(prefix="ls-ops-", dir="/tmp"))
        self.root.chmod(0o700)
        (self.root / "owner.json").write_text(json.dumps({"kind": "langshift-owned-pg18.6", "uid": os.getuid(), "nonce": self.nonce}))
        (self.root / "owner.json").chmod(0o600)
        (self.root / "empty.pgpass").touch(mode=0o600)
        (self.root / "socket").mkdir(mode=0o700)
        try:
            self.run("initdb", "-D", self.root / "data", "-U", "lab_owner", "--encoding=UTF8", "--no-locale", "--auth-local=trust", "--auth-host=reject")
            config = self.root / "data/postgresql.conf"
            with config.open("a") as output:
                output.write(f"\nlisten_addresses = ''\nunix_socket_directories = '{self.root / 'socket'}'\nunix_socket_permissions = 0700\nlog_statement = 'none'\nlog_min_error_statement = 'panic'\nlog_parameter_max_length_on_error = 0\n")
            self.run("pg_ctl", "-D", self.root / "data", "-l", self.root / "postgres.log", "-w", "start")
            self.started = True
            with connect(self.root, "postgres") as conn:
                conn.execute("CREATE ROLE lab_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE")
            self.create_database("source")
            return self
        except BaseException:
            # A timed-out start can still have produced an owned postmaster.
            self.started = (self.root / "data/postmaster.pid").exists()
            self.__exit__(None, None, None)
            raise

    def create_database(self, name: str):
        if name not in {"source", "restored", "damaged"} or name in self.databases:
            raise RuntimeError("Only a fresh named laboratory target may be created")
        with connect(self.root, "postgres") as conn:
            conn.autocommit = True
            conn.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(name)))
            conn.execute(sql.SQL("REVOKE ALL ON DATABASE {} FROM PUBLIC").format(sql.Identifier(name)))
        self.databases.add(name)

    def __exit__(self, *exc):
        if self.root is None:
            return
        checked_root(str(self.root))
        marker = json.loads((self.root / "owner.json").read_text())
        if marker["nonce"] != self.nonce:
            raise RuntimeError("Ownership changed; refusing stop/delete")
        if self.started:
            self.run("pg_ctl", "-D", self.root / "data", "-m", "fast", "-w", "stop")
            self.started = False
        shutil.rmtree(self.root)
