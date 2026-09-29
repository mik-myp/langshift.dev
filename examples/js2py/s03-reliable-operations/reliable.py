"""One local DB transaction, not exactly-once delivery or a blind retry loop."""
from datetime import timedelta
import hashlib
import json
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from authorization import create_task, guard_project
from models import TaskOperation
from schemas import TaskInput, TaskPublic
from security import utc_now

OPERATION = "create-task-v1"


def parse_key(value: str | None) -> UUID:
    try:
        key = UUID(value) if isinstance(value, str) else None
    except ValueError:
        key = None
    if key is None or key.version != 4 or str(key) != value:
        raise HTTPException(422, "Idempotency-Key must be a canonical UUIDv4")
    return key


def payload_digest(payload: TaskInput) -> str:
    canonical = json.dumps(payload.model_dump(mode="json"), sort_keys=True,
                           separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def create_task_once(session: Session, actor_id: int, project_id: int,
                     payload: TaskInput, key: UUID, ttl: int):
    # Must happen on EVERY call, before a stored response can escape.
    guard_project(session, actor_id, project_id)
    digest = payload_digest(payload)
    now = utc_now()
    identity = (actor_id, project_id, OPERATION, key)
    statement = insert(TaskOperation).values(actor_id=actor_id, project_id=project_id,
        operation=OPERATION, key=key, request_digest=digest, response_body={}, response_status=201,
        created_at=now, expires_at=now + timedelta(seconds=ttl))
    claimed = session.scalar(statement.on_conflict_do_nothing(
        index_elements=["actor_id", "project_id", "operation", "key"]).returning(TaskOperation.key))
    if claimed is None:
        # A new statement under READ COMMITTED sees the winner after the unique
        # index wait. There is no in-memory lock/dict standing in for this guarantee.
        receipt = session.scalar(select(TaskOperation).where(
            TaskOperation.actor_id == actor_id, TaskOperation.project_id == project_id,
            TaskOperation.operation == OPERATION, TaskOperation.key == key).with_for_update())
        if receipt is None:
            # A concurrent operator purge may have removed an expired receipt.
            # Do not silently create another task in this uncertain branch.
            raise HTTPException(409, "Receipt unavailable; reconcile before retrying")
        if receipt.expires_at <= utc_now():
            raise HTTPException(409, "Idempotency key expired; reconcile before a new operation")
        if receipt.request_digest != digest:
            raise HTTPException(409, "Idempotency key already used for a different payload")
        return TaskPublic.model_validate(receipt.response_body), True
    record = create_task(session, actor_id, project_id, payload)
    public = TaskPublic.model_validate(record)
    receipt = session.get(TaskOperation, identity)
    receipt.response_body = public.model_dump(mode="json")
    session.flush()
    # Endpoint commits after this function returns. A raised error before that
    # commit removes BOTH task and pending receipt. Never commit the {} placeholder.
    return public, False
