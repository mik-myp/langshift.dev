"""Owned, loopback-isolated PostgreSQL sandbox. Never selects an existing cluster."""
import argparse
import json
import os
from pathlib import Path
import secrets
import shlex
import shutil
import socket
import subprocess
import tempfile
import psycopg
from sqlalchemy import URL
from isolation import clear_libpq_environment, tool_environment

STATE = Path(".lab-state.json")


def binary(name: str) -> str:
    path = shutil.which(name) or str(Path("/opt/homebrew/bin") / name)
    if not Path(path).is_file():
        raise RuntimeError(f"PostgreSQL tool missing: {name}")
    return path


def run_tool(args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=60, env=tool_environment())
    if result.returncode:
        # Do not spill configuration, SQL or possible credentials from tool logs.
        raise RuntimeError(f"Owned PostgreSQL operation failed: {Path(args[0]).name}")
    return result


class OwnedCluster:
    def __init__(self):
        self.root = Path(tempfile.mkdtemp(prefix="ls-sec-", dir="/tmp")).resolve()
        self.root.chmod(0o700)
        self.owner = secrets.token_hex(16)
        self.uid = os.getuid()
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            self.port = listener.getsockname()[1]
        self.data = self.root / "data"
        self.socket_dir = self.root / "socket"
        self.socket_dir.mkdir(mode=0o700)
        (self.root / "owner.json").write_text(json.dumps(self.description()))
        (self.root / "owner.json").chmod(0o600)

    def description(self):
        return {"root": str(self.root), "owner": self.owner, "uid": self.uid, "port": self.port}

    def verify_ownership(self):
        if (self.root.parent != Path("/tmp").resolve() or not self.root.name.startswith("ls-sec-")
                or self.root.is_symlink() or self.uid != os.getuid()):
            raise RuntimeError("Refusing an unowned cluster path")
        if json.loads((self.root / "owner.json").read_text()) != self.description():
            raise RuntimeError("Cluster ownership marker mismatch")
        pid_file = self.data / "postmaster.pid"
        if pid_file.exists() and Path(pid_file.read_text().splitlines()[1]).resolve() != self.data:
            raise RuntimeError("Postmaster data directory mismatch")

    def start(self):
        clear_libpq_environment()
        self.verify_ownership()
        if "18.6" not in run_tool([binary("postgres"), "--version"]).stdout:
            raise RuntimeError("This lab requires the verified PostgreSQL 18.6 binary")
        run_tool([binary("initdb"), "-D", str(self.data), "-U", "lab_owner", "--auth-local=trust",
                  "--auth-host=reject", "--encoding=UTF8", "--locale=C"])
        options = (f"-k {self.socket_dir} -p {self.port} -c listen_addresses='' -c timezone=UTC "
                   "-c log_statement=none -c log_min_error_statement=panic "
                   "-c log_parameter_max_length_on_error=0")
        run_tool([binary("pg_ctl"), "-D", str(self.data), "-l", str(self.root / "postgres.log"),
                  "-o", options, "-w", "start"])
        with psycopg.connect(host=str(self.socket_dir), port=self.port, user="lab_owner",
                             dbname="postgres", autocommit=True) as connection:
            assert connection.execute("SHOW server_version_num").fetchone()[0] == "180006"
            assert connection.execute("SHOW listen_addresses").fetchone()[0] == ""
            connection.execute("CREATE DATABASE security_lab")
        return self

    def url(self, database="security_lab"):
        return URL.create("postgresql+psycopg", username="lab_owner", database=database,
                          query={"host": str(self.socket_dir), "port": str(self.port)}).render_as_string()

    def restart(self):
        self.verify_ownership()
        run_tool([binary("pg_ctl"), "-D", str(self.data), "-l", str(self.root / "postgres.log"),
                  "-w", "-m", "fast", "restart"])

    def stop(self):
        self.verify_ownership()
        if (self.data / "postmaster.pid").exists():
            run_tool([binary("pg_ctl"), "-D", str(self.data), "-w", "-m", "fast", "stop"])
        status = subprocess.run([binary("pg_ctl"), "-D", str(self.data), "status"], capture_output=True, env=tool_environment())
        if (self.data / "postmaster.pid").exists() or status.returncode not in (3, 4):
            raise RuntimeError("Stop not confirmed; owned directory retained")
        shutil.rmtree(self.root)  # Only this verified mkdtemp directory, after confirmed stop.

    def __enter__(self):
        try:
            return self.start()
        except BaseException:
            self.stop()
            raise

    def __exit__(self, exc_type, exc, traceback):
        self.stop()

    @classmethod
    def attach(cls, state):
        obj = cls.__new__(cls)
        obj.root = Path(state["root"])
        obj.owner, obj.uid, obj.port = state["owner"], state["uid"], state["port"]
        obj.data, obj.socket_dir = obj.root / "data", obj.root / "socket"
        obj.verify_ownership()
        return obj


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "status", "restart", "stop"])
    action = parser.parse_args().action
    if action == "start":
        if STATE.exists():
            raise SystemExit("State exists; inspect/stop your owned cluster first")
        cluster = OwnedCluster()
        try:
            cluster.start()
            with os.fdopen(os.open(STATE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as stream:
                json.dump(cluster.description(), stream)
        except BaseException:
            cluster.stop()
            raise
        print("export DATABASE_URL=" + shlex.quote(cluster.url()))
        print("# Copy only the export above into your shell. Unix socket only; no TCP listener.")
    else:
        if not STATE.exists():
            raise SystemExit("No owned cluster state in this working directory")
        cluster = OwnedCluster.attach(json.loads(STATE.read_text()))
        if action == "stop":
            cluster.stop()
            STATE.unlink()
            print("Owned cluster stopped and removed")
        elif action == "restart":
            cluster.restart()
            print("Owned cluster restarted; committed data retained")
        else:
            run_tool([binary("pg_ctl"), "-D", str(cluster.data), "status"])
            print("Owned cluster is running; PostgreSQL Unix socket port", cluster.port)
            print("export DATABASE_URL=" + shlex.quote(cluster.url()))


if __name__ == "__main__":
    main()
