from uuid import uuid4
import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from models import Project, ProjectMember, Task
from authorization import create_project


@pytest.fixture
def workspace(api, accounts):
    tokens = {name: api.token(name, accounts.password) for name in ("Alice", "Bob", "Carol")}
    projects = {name: api.request("POST", "/projects", {"name": name + " private"}, tokens[name]).body["id"]
                for name in ("Alice", "Bob")}
    task = api.request("POST", f"/projects/{projects['Bob']}/tasks", {"title": "Bob private"},
                       tokens["Bob"], str(uuid4())).body["id"]
    return tokens, projects, task


def test_project_owner_created_atomically_and_identity_server_owned(api, accounts, database):
    token = api.token("Alice", accounts.password)
    for forged in ({"name": "x", "created_by": accounts.Bob}, {"name": "x", "owner_id": accounts.Bob}):
        assert api.request("POST", "/projects", forged, token).status == 422
    result = api.request("POST", "/projects", {"name": "Alice project"}, token)
    assert result.status == 201 and result.body["created_by"] == accounts.Alice
    with Session(database) as session:
        member = session.get(ProjectMember, (result.body["id"], accounts.Alice))
        assert member.role == "owner"
    assert api.request("POST", "/projects", {"name": "anonymous"}).status == 401


@pytest.mark.parametrize("method,suffix,body", [
    ("GET", "", None), ("PATCH", "", {"name": "stolen"}), ("DELETE", "", None),
    ("GET", "/members", None), ("POST", "/members", {"user_id": 1}),
    ("DELETE", "/members/2", None), ("GET", "/tasks", None),
    ("POST", "/tasks", {"title": "stolen"}), ("GET", "/tasks/TASK", None),
    ("PATCH", "/tasks/TASK", {"status": "done"}), ("DELETE", "/tasks/TASK", None),
])
def test_alice_knowing_bob_ids_still_cannot_access(api, workspace, method, suffix, body):
    tokens, projects, task = workspace
    suffix = suffix.replace("TASK", str(task))
    result = api.request(method, f"/projects/{projects['Bob']}" + suffix, body, tokens["Alice"], str(uuid4()))
    assert result.status == 404


def test_scoped_project_list_and_cross_parent_task(api, workspace):
    tokens, projects, task = workspace
    result = api.request("GET", "/projects?limit=1&offset=0", token=tokens["Alice"])
    assert result.status == 200 and result.body["total"] == 1
    assert [p["id"] for p in result.body["items"]] == [projects["Alice"]]
    for method, body in [("GET", None), ("PATCH", {"status": "done"}), ("DELETE", None)]:
        assert api.request(method, f"/projects/{projects['Alice']}/tasks/{task}", body, tokens["Alice"]).status == 404
    assert api.request("GET", "/projects?limit=101", token=tokens["Alice"]).status == 422


def test_member_cannot_grant_roles_or_edit_others_but_owner_can(api, workspace, accounts):
    tokens, projects, task = workspace
    base = f"/projects/{projects['Bob']}"
    assert api.request("POST", base + "/members", {"user_id": accounts.Alice, "role": "owner"}, tokens["Bob"]).status == 422
    assert api.request("POST", base + "/members", {"user_id": accounts.Alice}, tokens["Bob"]).status == 201
    assert api.request("POST", base + "/members", {"user_id": accounts.Alice}, tokens["Bob"]).status == 409
    assert api.request("POST", base + "/members", {"user_id": accounts.Carol}, tokens["Alice"]).status == 403
    assert api.request("PATCH", base, {"name": "rename"}, tokens["Alice"]).status == 403
    assert api.request("DELETE", base, token=tokens["Alice"]).status == 403
    assert api.request("PATCH", base + f"/tasks/{task}", {"status": "done"}, tokens["Alice"]).status == 403
    assert api.request("DELETE", base + f"/tasks/{task}", token=tokens["Alice"]).status == 403
    for forged in ({"title": "forged", "created_by": accounts.Bob}, {"title": "forged", "user_id": accounts.Bob}):
        assert api.request("POST", base + "/tasks", forged, tokens["Alice"], str(uuid4())).status == 422
    created = api.request("POST", base + "/tasks", {"title": "  Mine  ", "description": "keep"},
                          tokens["Alice"], str(uuid4()))
    assert created.status == 201 and created.body["created_by"] == accounts.Alice and created.body["title"] == "  Mine  "
    own_path = base + f"/tasks/{created.body['id']}"
    patched = api.request("PATCH", own_path, {"status": "doing"}, tokens["Alice"])
    assert patched.status == 200 and patched.body["description"] == "keep"
    cleared = api.request("PATCH", own_path, {"description": None, "minutes": 0}, tokens["Alice"])
    assert cleared.status == 200 and cleared.body["description"] is None
    assert api.request("PATCH", own_path, {"minutes": True}, tokens["Alice"]).status == 422
    assert api.request("PATCH", own_path, {"created_by": accounts.Bob}, tokens["Alice"]).status == 422
    assert api.request("PATCH", own_path, {"title": None}, tokens["Alice"]).status == 422
    assert api.request("DELETE", own_path, token=tokens["Bob"]).status == 204


def test_owner_cannot_be_removed_and_removed_member_loses_access_immediately(api, workspace, accounts):
    tokens, projects, task = workspace
    base = f"/projects/{projects['Bob']}"
    assert api.request("DELETE", base + f"/members/{accounts.Bob}", token=tokens["Bob"]).status == 409
    assert api.request("POST", base + "/members", {"user_id": accounts.Alice}, tokens["Bob"]).status == 201
    assert api.request("GET", base + f"/tasks/{task}", token=tokens["Alice"]).status == 200
    assert api.request("DELETE", base + f"/members/{accounts.Alice}", token=tokens["Bob"]).status == 204
    assert api.request("GET", "/users/me", token=tokens["Alice"]).status == 200
    assert api.request("GET", base, token=tokens["Alice"]).status == 404
    assert api.request("GET", base + f"/tasks/{task}", token=tokens["Alice"]).status == 404
    assert api.request("POST", base + "/tasks", {"title": "late"}, tokens["Alice"], str(uuid4())).status == 404


def test_second_step_failure_rolls_back_project_and_owner(database, accounts):
    with pytest.raises(IntegrityError):
        with Session(database) as session, session.begin():
            project = Project(name="must roll back", created_by=accounts.Alice)
            session.add(project)
            session.flush()
            session.add(ProjectMember(project_id=project.id, user_id=999999, role="owner"))
            session.flush()
    with Session(database) as session:
        assert session.scalar(select(Project).where(Project.name == "must roll back")) is None
        assert session.query(ProjectMember).count() == 0
    with Session(database) as session, session.begin():
        project = create_project(session, accounts.Alice, "recovered")
        assert session.get(ProjectMember, (project.id, accounts.Alice)).role == "owner"


def test_unique_owner_is_a_database_guard(api, workspace, accounts, database):
    tokens, projects, task = workspace
    with pytest.raises(IntegrityError):
        with Session(database) as session, session.begin():
            session.add(ProjectMember(project_id=projects["Bob"], user_id=accounts.Alice, role="owner"))
            session.flush()
    assert api.request("GET", f"/projects/{projects['Bob']}", token=tokens["Bob"]).status == 200


def test_project_delete_removes_children_in_one_transaction(api, workspace, accounts, database):
    tokens, projects, task = workspace
    base = f"/projects/{projects['Bob']}"
    assert api.request("POST", base + "/members", {"user_id": accounts.Alice}, tokens["Bob"]).status == 201
    result = api.request("DELETE", base, token=tokens["Bob"])
    assert result.status == 204 and result.body_bytes == 0
    with Session(database) as session:
        assert session.get(Project, projects["Bob"]) is None
        assert session.get(Task, task) is None
        assert session.query(ProjectMember).filter_by(project_id=projects["Bob"]).count() == 0
    assert api.request("GET", base, token=tokens["Bob"]).status == 404


def test_object_validation_never_echoes_secret_body_query_or_path(api, workspace):
    import json
    import secrets
    tokens, projects, task = workspace
    marker = "PRIVATE-" + secrets.token_hex(12)
    api.secrets.append(marker)
    base = f"/projects/{projects['Bob']}"
    for result in [
        api.request("POST", base+"/tasks", {"title":"x", "minutes":marker}, tokens["Bob"], str(uuid4())),
        api.request("POST", base+"/members", {"user_id":1, marker:marker}, tokens["Bob"]),
        api.request("GET", "/projects?limit="+marker, token=tokens["Bob"]),
        api.request("GET", "/projects/"+marker, token=tokens["Bob"]),
    ]:
        assert result.status == 422 and marker not in json.dumps(result.body)
        assert '"input"' not in json.dumps(result.body)


def test_real_inflight_project_write_orders_member_removal(api, workspace, accounts, database, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    import json
    import os
    from pathlib import Path
    import threading
    import time
    from authorization import create_task, guard_project, remove_member, require_owner
    from schemas import TaskInput
    from security import authenticate
    tokens, projects, task = workspace
    project_id = projects["Bob"]
    base = f"/projects/{project_id}"
    assert api.request("POST", base+"/members", {"user_id":accounts.Alice}, tokens["Bob"]).status == 201
    first = Session(database)
    first.begin()
    actor, credential = authenticate(first, "Bearer " + tokens["Alice"])
    guard_project(first, actor.id, project_id)
    first_pid = first.scalar(text("SELECT pg_backend_pid()"))
    created = create_task(first, actor.id, project_id, TaskInput(title="Authorized before removal"))
    created_id = created.id
    started, state = threading.Event(), {}
    def remove():
        with Session(database) as second, second.begin():
            second.execute(text("SET LOCAL lock_timeout = '8s'"))
            actor, credential = authenticate(second, "Bearer " + tokens["Bob"])
            state["pid"] = second.scalar(text("SELECT pg_backend_pid()"))
            started.set()
            project, member = guard_project(second, actor.id, project_id, exclusive=True)
            require_owner(member)
            remove_member(second, project_id, accounts.Alice)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(remove)
        try:
            assert started.wait(3)
            blocked = False
            for _ in range(100):
                with database.connect() as observer:
                    blockers = observer.scalar(text("SELECT pg_blocking_pids(:pid)"), {"pid":state["pid"]})
                if first_pid in blockers:
                    blocked = True
                    break
                time.sleep(.02)
            assert blocked and first_pid != state["pid"]
            first.commit()
            future.result(timeout=10)
        finally:
            first.rollback()
            first.close()
    assert api.request("GET", base+f"/tasks/{created_id}", token=tokens["Alice"]).status == 404
    assert api.request("GET", base+f"/tasks/{created_id}", token=tokens["Bob"]).status == 200
    assert api.request("GET", "/users/me", token=tokens["Alice"]).status == 200
    directory = Path(os.environ.get("SECURITY_EVIDENCE_DIR", str(tmp_path)))
    directory.mkdir(parents=True, exist_ok=True)
    (directory / (Path.cwd().name + "-member-removal-race.json")).write_text(json.dumps(
        {"prior_writer_pid":first_pid,"removal_pid":state["pid"],"observed_project_lock_wait":blocked,
         "prior_write_committed":True,"removed_actor_http":404,"owner_http":200,
         "boundary":"No retroactive cancellation; requests admitted before removal may finish"},indent=2))
