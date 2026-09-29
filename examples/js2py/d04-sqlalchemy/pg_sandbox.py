"""Run a command inside a disposable PostgreSQL 18 cluster, never a user DB.

POSIX only. No TCP listener, Docker, brew services, or existing database URL.
The marker is an accident guard, not an authentication/security boundary.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import uuid


def binaries():
    directory = os.environ.get("PG_BIN")
    found = {}
    for name in ("postgres", "initdb", "pg_ctl", "psql"):
        path = str(Path(directory) / name) if directory else shutil.which(name)
        if not path and Path("/opt/homebrew/bin", name).is_file():
            path = str(Path("/opt/homebrew/bin", name))
        if not path or not Path(path).is_file():
            raise RuntimeError("Install PostgreSQL 18 binaries; set PG_BIN to their directory")
        found[name] = path
    for name in ("postgres", "initdb", "pg_ctl", "psql"):
        version = subprocess.check_output([found[name], "--version"], text=True).strip()
        if " 18." not in version:
            raise RuntimeError(f"Expected PostgreSQL 18 binaries: {version}")
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, help="Write cleanup proof outside the cluster")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("provide a command after --")
    tools = binaries()
    root = Path(tempfile.mkdtemp(prefix="ls-pg-", dir="/tmp")).resolve()
    root.chmod(0o700)
    data, sock = root / "data", root / "socket"
    sock.mkdir(mode=0o700)
    token = uuid.uuid4().hex
    marker = {"token": token, "root": str(root), "port": 55432, "owner": "lab_owner"}
    (root / "owner.json").write_text(json.dumps(marker))
    evidence = {"cluster": str(root), "socket": str(sock), "tcp": False,
                "server_version": None, "command_exit": None, "stopped": False,
                "removed": False, "status_after_stop": None}
    # Ignore credentials/connection settings inherited from the user's terminal.
    env = {k: v for k, v in os.environ.items()
           if not k.startswith("PG") and k not in
           {"DATABASE_URL", "TEST_DATABASE_URL", "LAB_DATABASE_URL", "LAB_CLUSTER_ROOT",
            "LAB_CLUSTER_TOKEN"}}
    child = None
    started = False
    def interrupt(signum, frame):
        raise KeyboardInterrupt
    old_term = signal.signal(signal.SIGTERM, interrupt)
    code = 1
    try:
        subprocess.run([tools["initdb"], "-D", str(data), "-U", "lab_admin",
                        "--auth-local=trust", "--auth-host=reject", "--encoding=UTF8",
                        "--no-locale"], env=env, check=True, stdout=subprocess.DEVNULL)
        with (data / "postgresql.conf").open("a") as file:
            file.write(f"\nlisten_addresses = ''\nunix_socket_directories = '{sock}'\n"
                       "unix_socket_permissions = 0700\nport = 55432\nmax_connections = 30\n")
        subprocess.run([tools["pg_ctl"], "-D", str(data), "-l", str(root / "server.log"),
                        "-w", "start"], env=env, check=True, stdout=subprocess.DEVNULL)
        started = True
        def sql(statement):
            return subprocess.check_output(
                [tools["psql"], "-X", "-h", str(sock), "-p", "55432", "-U", "lab_admin",
                 "-d", "postgres", "-v", "ON_ERROR_STOP=1", "-Atc", statement], env=env, text=True).strip()
        evidence["server_version"] = sql("SHOW server_version_num")
        sql("CREATE ROLE lab_owner LOGIN NOSUPERUSER CREATEDB NOCREATEROLE")
        database = "js2py_lab_" + uuid.uuid4().hex
        sql(f'CREATE DATABASE "{database}" OWNER lab_owner')
        from urllib.parse import urlencode
        env.update(LAB_DATABASE_URL=f"postgresql+psycopg://lab_owner@/{database}?" +
                   urlencode({"host": str(sock), "port": 55432}),
                   LAB_CLUSTER_ROOT=str(root), LAB_CLUSTER_TOKEN=token)
        print(f"sandbox: PostgreSQL {evidence['server_version']}; private socket; no TCP", flush=True)
        child = subprocess.Popen(command, env=env)
        code = child.wait()
        evidence["command_exit"] = code
    except KeyboardInterrupt:
        code = 130
        evidence["command_exit"] = code
    finally:
        # Keep cleanup from being interrupted a second time; never signal other clusters.
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        if started or (data / "postmaster.pid").exists():
            result = subprocess.run([tools["pg_ctl"], "-D", str(data), "-w", "-m", "fast", "stop"],
                                    env=env, capture_output=True, text=True)
            evidence["stop_exit"] = result.returncode
            status = subprocess.run([tools["pg_ctl"], "-D", str(data), "status"],
                                    env=env, capture_output=True, text=True)
            evidence["status_after_stop"] = status.returncode
            evidence["stopped"] = status.returncode == 3 and not (data / "postmaster.pid").exists()
        else:
            evidence["stopped"] = True
        if evidence["stopped"]:
            shutil.rmtree(root)
            evidence["removed"] = not root.exists()
        else:
            code = 1
            print(f"STOP FAILED: retained owned cluster/logs at {root}", file=sys.stderr)
        if args.evidence:
            args.evidence.parent.mkdir(parents=True, exist_ok=True)
            args.evidence.write_text(json.dumps(evidence, indent=2) + "\n")
        print("cleanup: " + json.dumps(evidence, sort_keys=True), flush=True)
        signal.signal(signal.SIGTERM, old_term)
    return code


if __name__ == "__main__":
    sys.exit(main())
