"""Own one disposable PostgreSQL 18.6 cluster; never use DATABASE_URL.

All destructive operations are restricted to our marker-checked /tmp directory.
Stop retains files for recovery. Nothing invokes brew services, kill or rm -rf.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile

import psycopg
from psycopg.conninfo import make_conninfo

LAB = Path(__file__).resolve().parent
STATE = LAB / ".lab-state.json"
MARKER = "langshift-owned-cluster.json"
VERSION_NUM = 180006


# PGHOST is safe only because every SQL DSN supplies an explicit private socket.
# PG_BIN selects executables, not a libpq connection parameter. Fail closed for
# all other PG* names (even empty/unknown ones), including future libpq defaults.
ALLOWED_PG_ENV = frozenset({"PGHOST", "PG_BIN"})


def check_environment():
    rejected = sorted(name for name in os.environ
                      if name.startswith("PG") and name not in ALLOWED_PG_ENV)
    if rejected:
        # Never echo values: these may contain passwords or service credentials.
        raise RuntimeError("Refusing implicit PostgreSQL environment: " + ", ".join(rejected))


def child_environment():
    # Do not mutate os.environ: D03 can open connections from multiple threads.
    return {name: value for name, value in os.environ.items()
            if not name.startswith("PG") and name != "DATABASE_URL"}


def run(*args, check=True):
    result = subprocess.run(args, check=False, text=True, capture_output=True,
                            env=child_environment())
    if check and result.returncode:
        raise RuntimeError(
            f"{Path(args[0]).name} exited {result.returncode}:\n"
            f"{result.stdout}{result.stderr}"
        )
    return result


def load_state():
    if STATE.is_symlink():
        raise RuntimeError("Refusing a symlink state file")
    if not STATE.exists():
        raise RuntimeError("No owned cluster. Run labctl.py start first")
    state = json.loads(STATE.read_text())
    root = Path(state["root"])
    if root.is_symlink() or root.resolve().parent != Path("/tmp").resolve():
        raise RuntimeError("Refusing a cluster outside the owned /tmp root")
    if not root.name.startswith("lsdb-"):
        raise RuntimeError("Unexpected cluster directory name")
    metadata = root.stat()
    if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) != 0o700:
        raise RuntimeError("Cluster root must be owned by this OS user, mode 0700")
    marker = root / MARKER
    if marker.is_symlink() or json.loads(marker.read_text()) != state:
        raise RuntimeError("Ownership marker mismatch; no database action performed")
    if state["lab"] != str(LAB):
        raise RuntimeError("This cluster belongs to a different lab directory")
    for child in ("data", "socket"):
        path = root / child
        if path.is_symlink() or path.resolve().parent != root.resolve():
            raise RuntimeError("Refusing redirected cluster paths")
    return state


def empty_passfile(state):
    # Also works for previously created, marker-checked clusters. Never consult
    # HOME/.pgpass; never follow a passfile symlink or reuse nonempty credentials.
    path = Path(state["root"]) / "empty.pgpass"
    fd = os.open(path, os.O_RDONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        metadata = os.fstat(fd)
        if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid()
                or stat.S_IMODE(metadata.st_mode) != 0o600 or metadata.st_size != 0):
            raise RuntimeError("Refusing unsafe lab passfile")
    finally:
        os.close(fd)
    return str(path)


def raw_dsn(state, admin=False):
    check_environment()
    return make_conninfo(
        host=str(Path(state["root"]) / "socket"), port=state["port"],
        dbname="langshift_lab", user=state["admin"] if admin else "lab_student",
        passfile=empty_passfile(state),
        connect_timeout=3, application_name=LAB.name,
        options="-c timezone=UTC -c statement_timeout=8000 -c lock_timeout=3000",
    )


def check_pid_file(state):
    root = Path(state["root"])
    pid_file = root / "data/postmaster.pid"
    if pid_file.is_symlink():
        raise RuntimeError("Refusing redirected PID file")
    if pid_file.exists():
        lines = pid_file.read_text().splitlines()
        if (Path(lines[1]).resolve() != (root / "data").resolve()
                or lines[3] != str(state["port"])
                or Path(lines[4]).resolve() != (root / "socket").resolve()):
            raise RuntimeError("PID file does not describe the owned server")


def verify_server(state):
    check_environment()
    check_pid_file(state)
    with psycopg.connect(raw_dsn(state, admin=True), autocommit=True) as conn:
        actual = conn.execute("""
            SELECT current_setting('data_directory'),
                   current_setting('server_version_num')::int,
                   system_identifier::text
            FROM pg_control_system()
        """).fetchone()
    if (Path(actual[0]).resolve() != Path(state["root"]) / "data"
            or actual[1] != VERSION_NUM
            or actual[2] != state["system_identifier"]):
        raise RuntimeError("Wrong server identity/version; refusing SQL")


def connect(*, autocommit=False):
    check_environment()
    state = load_state()
    verify_server(state)
    return psycopg.connect(raw_dsn(state), autocommit=autocommit)


def start():
    check_environment()
    if STATE.exists() or STATE.is_symlink():
        state = load_state()
        check_pid_file(state)
        result = run(str(Path(state["pg_bin"]) / "pg_ctl"), "-D",
                     str(Path(state["root"]) / "data"), "status", check=False)
        if result.returncode == 3:
            run(str(Path(state["pg_bin"]) / "pg_ctl"), "-D",
                str(Path(state["root"]) / "data"), "-l",
                str(Path(state["root"]) / "server.log"), "-w", "-t", "15", "start")
        elif result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout)
        verify_server(state)
        print("owned cluster ready (existing data retained)")
        return
    default = Path(shutil.which("initdb") or "/opt/homebrew/bin/initdb").parent
    pg_bin = Path(os.environ.get("PG_BIN", str(default))).resolve()
    for tool in ("postgres", "initdb", "pg_ctl", "psql"):
        version = run(str(pg_bin / tool), "--version").stdout.strip()
        if " 18.6" not in version:
            raise RuntimeError(f"Expected PostgreSQL 18.6: {version}")
    root = Path(tempfile.mkdtemp(prefix="lsdb-", dir="/tmp")).resolve()
    root.chmod(0o700)
    (root / "socket").mkdir(mode=0o700)
    state = {
        "root": str(root), "lab": str(LAB), "token": secrets.token_hex(16),
        "admin": "lab_admin_" + secrets.token_hex(6), "pg_bin": str(pg_bin),
        "port": 49152 + secrets.randbelow(12000),
    }
    # Persist ownership before starting so partial failures remain recoverable.
    def save():
        text = json.dumps(state, indent=2) + "\n"
        (root / MARKER).write_text(text)
        STATE.write_text(text)
        STATE.chmod(0o600)
    save()
    try:
        run(str(pg_bin / "initdb"), "-D", str(root / "data"), "-U", state["admin"],
            "--auth-local=trust", "--auth-host=reject", "--encoding=UTF8", "--no-locale")
        with (root / "data/postgresql.conf").open("a") as config:
            config.write(f"\nlisten_addresses = ''\nport = {state['port']}\n")
            config.write(f"unix_socket_directories = '{root / 'socket'}'\n")
            config.write("unix_socket_permissions = 0700\ntimezone = 'UTC'\n")
        run(str(pg_bin / "pg_ctl"), "-D", str(root / "data"), "-l",
            str(root / "server.log"), "-w", "-t", "15", "start")
        admin_dsn = make_conninfo(raw_dsn(state, admin=True), dbname="postgres")
        with psycopg.connect(admin_dsn, autocommit=True) as conn:
            state["system_identifier"] = conn.execute(
                "SELECT system_identifier::text FROM pg_control_system()"
            ).fetchone()[0]
            save()
            conn.execute("CREATE ROLE lab_student LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE")
            conn.execute("CREATE DATABASE langshift_lab OWNER lab_student")
        verify_server(state)
    except BaseException:
        # This exact new root was allocated above; never stop any default service.
        run(str(pg_bin / "pg_ctl"), "-D", str(root / "data"),
            "-m", "fast", "-w", "-t", "15", "stop", check=False)
        raise
    print("owned cluster ready: PostgreSQL 18.6; TCP disabled")
    print(f"root={root}")


def reset():
    with connect() as conn:
        conn.execute("DROP TABLE IF EXISTS tasks, project_members, projects, users")
        conn.execute((LAB / "sql/schema.sql").read_text())
        conn.execute((LAB / "sql/seed.sql").read_text())


def stop():
    state = load_state()
    check_pid_file(state)
    pg_ctl = str(Path(state["pg_bin"]) / "pg_ctl")
    data = str(Path(state["root"]) / "data")
    result = run(pg_ctl, "-D", data, "status", check=False)
    if result.returncode == 3:
        print("owned cluster already stopped; files retained")
        return
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)
    # Keep the identity check, but run it in a clean child so a poisoned shell
    # cannot prevent cleanup. No process-global environment mutation/race, and
    # no SQL against any target other than this lab's marker-checked socket.
    run(sys.executable, str(LAB / "labctl.py"), "dsn")
    print(run(pg_ctl, "-D", data, "-m", "fast", "-w", "-t", "15", "stop").stdout.strip())
    if run(pg_ctl, "-D", data, "status", check=False).returncode != 3:
        raise RuntimeError("Owned server did not stop")
    print("owned cluster stopped; pg_ctl status=3; files retained")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["start", "status", "dsn", "reset", "stop", "psql"])
    parser.add_argument("--yes-reset", action="store_true")
    parser.add_argument("--file")
    args = parser.parse_args()
    if args.command not in {"stop", "status"}:
        check_environment()
    if args.command == "start":
        start()
    elif args.command == "stop":
        stop()
    elif args.command == "reset":
        if not args.yes_reset:
            parser.error("reset destroys only this lab's tables; require --yes-reset")
        reset()
        print("schema + seed ready: users=2 projects=3 members=4 tasks=5")
    elif args.command == "status":
        state = load_state()
        check_pid_file(state)
        result = run(str(Path(state["pg_bin"]) / "pg_ctl"), "-D",
                     str(Path(state["root"]) / "data"), "status", check=False)
        if result.returncode not in (0, 3):
            raise RuntimeError(result.stderr or result.stdout)
        print(json.dumps({"root": state["root"], "running": result.returncode == 0,
                          "pg_ctl_status": result.returncode}))
    else:
        state = load_state()
        verify_server(state)
        if args.command == "dsn":
            print(raw_dsn(state))
        else:
            command = [str(Path(state["pg_bin"]) / "psql"), "-X", "-w", raw_dsn(state),
                       "-v", "ON_ERROR_STOP=1", "-P", "pager=off"]
            if args.file:
                command += ["-f", str(Path(args.file).resolve())]
            subprocess.run(command, check=True, env=child_environment())


if __name__ == "__main__":
    main()
