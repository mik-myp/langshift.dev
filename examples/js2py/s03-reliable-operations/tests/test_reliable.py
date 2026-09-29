from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from uuid import uuid4
import pytest
from fastapi import HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from models import Task, TaskOperation
from reliable import create_task_once
from schemas import TaskInput
from security import utc_now


@pytest.fixture
def project(api, accounts):
    alice, bob = api.token("Alice", accounts.password), api.token("Bob", accounts.password)
    result = api.request("POST", "/projects", {"name": "Reliable"}, alice)
    assert result.status == 201
    return result.body["id"], alice, bob


def count_tasks(database):
    with Session(database) as session:
        return session.scalar(select(func.count()).select_from(Task))


def test_replay_identical_and_default_normalization(api, project, database):
    pid, token, other = project
    path, key = f"/projects/{pid}/tasks", str(uuid4())
    first = api.request("POST", path, {"title": "  Keep  "}, token, key)
    replay = api.request("POST", path, {"title": "  Keep  ", "status": "todo", "minutes": 0,
                        "priority": 0, "description": None, "due_at": None}, token, key)
    assert first.status == replay.status == 201 and first.body == replay.body
    assert first.headers["idempotency-replayed"] == "false"
    assert replay.headers["idempotency-replayed"] == "true" and count_tasks(database) == 1


def test_mismatch_conflict_and_missing_or_noncanonical_key(api, project, database):
    pid, token, other = project
    path, key = f"/projects/{pid}/tasks", str(uuid4())
    for bad in (None, "bad", "123e4567-e89b-12d3-a456-426614174000", key.upper()):
        assert api.request("POST", path, {"title": "x"}, token, bad).status == 422
    assert api.request("POST", path, {"title": "first"}, token, key).status == 201
    assert api.request("POST", path, {"title": "different"}, token, key).status == 409
    assert count_tasks(database) == 1


def test_key_scope_includes_actor_and_project(api, project, accounts, database):
    pid, alice, bob = project
    assert api.request("POST", f"/projects/{pid}/members", {"user_id": accounts.Bob}, alice).status == 201
    second_pid = api.request("POST", "/projects", {"name": "Second"}, alice).body["id"]
    key = str(uuid4())
    identities = set()
    for project_id, token in [(pid, alice), (pid, bob), (second_pid, alice)]:
        result = api.request("POST", f"/projects/{project_id}/tasks", {"title": "Scoped"}, token, key)
        assert result.status == 201
        identities.add(result.body["id"])
    assert len(identities) == 3 and count_tasks(database) == 3


def test_replay_rechecks_membership_and_session_generation(api, project, accounts):
    pid, owner, member = project
    assert api.request("POST", f"/projects/{pid}/members", {"user_id": accounts.Bob}, owner).status == 201
    path, key = f"/projects/{pid}/tasks", str(uuid4())
    assert api.request("POST", path, {"title": "Member task"}, member, key).status == 201
    assert api.request("DELETE", f"/projects/{pid}/members/{accounts.Bob}", token=owner).status == 204
    assert api.request("POST", path, {"title": "Member task"}, member, key).status == 404
    assert api.request("GET", "/users/me", token=member).status == 200
    owner_key = str(uuid4())
    assert api.request("POST", path, {"title": "Owner task"}, owner, owner_key).status == 201
    assert api.request("POST", "/auth/logout-all", token=owner).status == 204
    assert api.request("POST", path, {"title": "Owner task"}, owner, owner_key).status == 401


def test_receipt_is_original_result_not_current_task(api, project):
    pid, token, other = project
    path, key = f"/projects/{pid}/tasks", str(uuid4())
    first = api.request("POST", path, {"title": "Original"}, token, key)
    task_path = path + f"/{first.body['id']}"
    assert api.request("PATCH", task_path, {"status": "done"}, token).status == 200
    replay = api.request("POST", path, {"title": "Original"}, token, key)
    assert replay.body == first.body and replay.body["status"] == "todo"
    assert api.request("GET", task_path, token=token).body["status"] == "done"


def test_expired_receipt_rejects_until_explicit_purge_then_no_dedup_guarantee(api, project, database, cluster):
    pid, token, other = project
    path, key = f"/projects/{pid}/tasks", str(uuid4())
    first = api.request("POST", path, {"title": "Retention"}, token, key)
    with Session(database) as session, session.begin():
        receipt = session.scalar(select(TaskOperation))
        receipt.created_at = utc_now() - timedelta(days=2)
        receipt.expires_at = utc_now() - timedelta(days=1)
    assert api.request("POST", path, {"title": "Retention"}, token, key).status == 409
    for flags in ([], ["--apply"]):
        result = subprocess.run([sys.executable, "purge_expired.py", *flags],
            env=dict(os.environ, DATABASE_URL=cluster.url()), capture_output=True, text=True, timeout=10)
        assert result.returncode == 0
    second = api.request("POST", path, {"title": "Retention"}, token, key)
    assert second.status == 201 and second.body["id"] != first.body["id"]
    assert count_tasks(database) == 2


def test_utc_offsets_normalize_for_idempotency_and_naive_time_rejected(api, project):
    pid, token, other = project
    path, key = f"/projects/{pid}/tasks", str(uuid4())
    first = api.request("POST", path, {"title": "UTC", "due_at": "2026-09-28T16:30:00+08:00"}, token, key)
    second = api.request("POST", path, {"title": "UTC", "due_at": "2026-09-28T08:30:00+00:00"}, token, key)
    assert first.status == second.status == 201 and first.body == second.body
    assert first.body["due_at"] == "2026-09-28T08:30:00Z"
    assert api.request("POST", path, {"title": "naive", "due_at": "2026-09-28T08:30:00"}, token, str(uuid4())).status == 422


def test_failure_before_commit_rolls_back_task_and_receipt(database, accounts, project):
    pid, token, other = project
    key = uuid4()
    with pytest.raises(RuntimeError, match="deliberate"):
        with Session(database) as session, session.begin():
            create_task_once(session, accounts.Alice, pid, TaskInput(title="Rollback"), key, 86400)
            raise RuntimeError("deliberate failure before commit")
    with Session(database) as session:
        assert session.scalar(select(func.count()).select_from(TaskOperation)) == 0
    assert count_tasks(database) == 0
    with Session(database) as session, session.begin():
        result, replayed = create_task_once(session, accounts.Alice, pid, TaskInput(title="Rollback"), key, 86400)
        assert not replayed  # Sequence gaps after rollback are normal, not duplicate tasks.


def test_two_simultaneous_http_calls_converge(api, project, database):
    pid, token, other = project
    path, key, gate = f"/projects/{pid}/tasks", str(uuid4()), threading.Barrier(2)
    def send():
        gate.wait(timeout=5)
        return api.request("POST", path, {"title": "HTTP race"}, token, key)
    with ThreadPoolExecutor(max_workers=2) as pool:
        left, right = [future.result(timeout=15) for future in [pool.submit(send), pool.submit(send)]]
    assert left.status == right.status == 201 and left.body == right.body
    assert sorted([left.headers["idempotency-replayed"], right.headers["idempotency-replayed"]]) == ["false", "true"]
    assert count_tasks(database) == 1


@pytest.mark.parametrize("mode", ["commit-identical", "commit-different", "rollback-identical"])
def test_real_two_connection_unique_wait_and_winner_outcome(database, accounts, project, mode, tmp_path):
    pid, token, other = project
    key, first = uuid4(), Session(database)
    first.begin()
    first_pid = first.scalar(text("SELECT pg_backend_pid()"))
    initial, _ = create_task_once(first, accounts.Alice, pid, TaskInput(title="Race"), key, 86400)
    initial_id = initial.id
    started, state = threading.Event(), {}
    def competitor():
        with Session(database) as second:
            try:
                with second.begin():
                    second.execute(text("SET LOCAL lock_timeout = '8s'"))
                    state["pid"] = second.scalar(text("SELECT pg_backend_pid()"))
                    started.set()
                    title = "Different" if mode == "commit-different" else "Race"
                    public, replayed = create_task_once(second, accounts.Alice, pid, TaskInput(title=title), key, 86400)
                    return 201, public.id, replayed
            except HTTPException as error:
                return error.status_code, None, None
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(competitor)
        try:
            assert started.wait(3)
            blocked = False
            for _ in range(100):
                with database.connect() as observer:
                    blockers = observer.scalar(text("SELECT pg_blocking_pids(:pid)"), {"pid": state["pid"]})
                if first_pid in blockers:
                    blocked = True
                    break
                time.sleep(.02)
            assert blocked and first_pid != state["pid"]
            if mode == "rollback-identical":
                first.rollback()
            else:
                first.commit()
            status, identity, replayed = future.result(timeout=10)
            if mode == "commit-identical":
                assert (status, identity, replayed) == (201, initial_id, True)
            elif mode == "commit-different":
                assert status == 409
            else:
                assert status == 201 and not replayed and identity != initial_id
            assert count_tasks(database) == 1
            evidence = {"mode": mode, "winner_pid": first_pid, "competitor_pid": state["pid"],
                        "observed_unique_index_lock_wait": blocked, "competitor_status": status,
                        "task_count": 1, "isolation": "read committed"}
            target = Path(os.environ.get("SECURITY_EVIDENCE_DIR", str(tmp_path)))
            target.mkdir(parents=True, exist_ok=True)
            (target / ("s03-race-" + mode + ".json")).write_text(json.dumps(evidence, indent=2))
        finally:
            first.rollback()
            first.close()


def test_receipt_survives_real_api_and_database_restarts(api, project, cluster, database):
    pid, token, other = project
    path, key = f"/projects/{pid}/tasks", str(uuid4())
    first = api.request("POST", path, {"title":"Committed receipt"}, token, key)
    api.restart()
    cluster.restart()
    replay = api.request("POST", path, {"title":"Committed receipt"}, token, key)
    assert first.status == replay.status == 201 and first.body == replay.body
    assert replay.headers["idempotency-replayed"] == "true"
    assert count_tasks(database) == 1
