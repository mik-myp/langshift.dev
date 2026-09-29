"""Real overlapping PostgreSQL sessions, bounded waits, no timing-only assertions."""
from concurrent.futures import ThreadPoolExecutor
from threading import Event
import time
from psycopg import IsolationLevel, errors
import labctl
from transactions import insert_project_and_owner


def failed_second_step():
    try:
        with labctl.connect() as conn:
            insert_project_and_owner(conn, "Broken", 1, 9999)
    except errors.ForeignKeyViolation as exc:
        state = exc.sqlstate
    else:
        raise AssertionError("The deliberate second-step failure did not occur")
    with labctl.connect(autocommit=True) as observer:
        residual = observer.execute("SELECT count(*) FROM projects WHERE name=%s", ("Broken",)).fetchone()[0]
        memberships = observer.execute("SELECT count(*) FROM project_members").fetchone()[0]
    return {"sqlstate": state, "projects_remaining": residual, "memberships": memberships}


def snapshot(isolation):
    with labctl.connect() as reader, labctl.connect() as writer:
        reader.isolation_level = isolation
        first = reader.execute("SELECT minutes FROM tasks WHERE id=1").fetchone()[0]
        writer.execute("UPDATE tasks SET minutes=minutes+10 WHERE id=1")
        writer.commit()
        second = reader.execute("SELECT minutes FROM tasks WHERE id=1").fetchone()[0]
    return [first, second]


def lost_update():
    with labctl.connect() as a, labctl.connect() as b:
        old_a = a.execute("SELECT minutes FROM tasks WHERE id=1").fetchone()[0]
        old_b = b.execute("SELECT minutes FROM tasks WHERE id=1").fetchone()[0]
        a.execute("UPDATE tasks SET minutes=%s WHERE id=1", (old_a + 5,))
        a.commit()
        b.execute("UPDATE tasks SET minutes=%s WHERE id=1", (old_b + 7,))
        b.commit()
    with labctl.connect(autocommit=True) as observer:
        return observer.execute("SELECT minutes FROM tasks WHERE id=1").fetchone()[0]


def wait_for_lock(pid):
    deadline = time.monotonic() + 2
    with labctl.connect(autocommit=True) as inspector:
        while time.monotonic() < deadline:
            row = inspector.execute("SELECT wait_event_type FROM pg_stat_activity WHERE pid=%s", (pid,)).fetchone()
            if row == ("Lock",):
                return True
            time.sleep(0.01)  # Poll observed state, not a guessed completion delay.
    raise AssertionError("Second session never entered an observed lock wait")


def overlapping_write(kind):
    if kind not in {"increment", "unique"}:
        raise ValueError("unknown scenario")
    ready = Event()
    info = {}
    def worker():
        try:
            with labctl.connect() as b:
                info["pid"] = b.info.backend_pid
                ready.set()
                if kind == "increment":
                    b.execute("UPDATE tasks SET minutes=minutes+7 WHERE id=1")
                else:
                    b.execute("INSERT INTO users(login) VALUES (%s)", ("race",))
            return "committed"
        except errors.UniqueViolation as exc:
            return exc.sqlstate
    with ThreadPoolExecutor(max_workers=1) as pool:
        with labctl.connect() as a:
            if kind == "increment":
                a.execute("UPDATE tasks SET minutes=minutes+5 WHERE id=1")
            else:
                a.execute("INSERT INTO users(login) VALUES (%s)", ("race",))
            future = pool.submit(worker)
            try:
                if not ready.wait(3):
                    raise AssertionError("Worker did not connect")
                observed = wait_for_lock(info["pid"])
                a.commit()
            finally:
                a.rollback()  # Releases A's locks even if an assertion fails.
            outcome = future.result(timeout=10)
    with labctl.connect(autocommit=True) as observer:
        query = ("SELECT minutes FROM tasks WHERE id=1" if kind == "increment" else
                 "SELECT count(*) FROM users WHERE login='race'")
        value = observer.execute(query).fetchone()[0]
    return {"lock_wait_observed": observed, "worker": outcome, "value": value}


def lock_timeout():
    with labctl.connect() as a, labctl.connect() as b:
        a.execute("SELECT id FROM tasks WHERE id=1 FOR UPDATE")
        b.execute("SET LOCAL lock_timeout='200ms'")
        try:
            b.execute("UPDATE tasks SET minutes=99 WHERE id=1")
        except errors.LockNotAvailable as exc:
            state = exc.sqlstate
            b.rollback()
        else:
            raise AssertionError("Expected a real row-lock timeout")
        a.rollback()
        recovered = b.execute("SELECT minutes FROM tasks WHERE id=1").fetchone()[0]
    return {"sqlstate": state, "minutes_after_rollback": recovered}


def serialization_conflict():
    with labctl.connect() as a, labctl.connect() as b:
        a.isolation_level = IsolationLevel.REPEATABLE_READ
        b.isolation_level = IsolationLevel.REPEATABLE_READ
        a.execute("SELECT minutes FROM tasks WHERE id=1").fetchone()
        b.execute("SELECT minutes FROM tasks WHERE id=1").fetchone()
        a.execute("UPDATE tasks SET minutes=minutes+5 WHERE id=1")
        a.commit()
        try:
            b.execute("UPDATE tasks SET minutes=minutes+7 WHERE id=1")
        except errors.SerializationFailure as exc:
            state = exc.sqlstate
            b.rollback()
        else:
            raise AssertionError("Expected conflicting repeatable-read update")
        # Start a NEW transaction; repeat the entire business decision using fresh data.
        fresh = b.execute("SELECT minutes FROM tasks WHERE id=1 FOR UPDATE").fetchone()[0]
        b.execute("UPDATE tasks SET minutes=%s WHERE id=1", (fresh + 7,))
        b.commit()
    return {"sqlstate": state, "after_full_retry": fresh + 7}
