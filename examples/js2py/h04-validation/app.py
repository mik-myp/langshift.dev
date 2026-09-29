from fastapi import FastAPI, HTTPException, Path, Query, Response

from models import TaskCreate, TaskPage, TaskPatch, TaskPublic, TaskStored

app = FastAPI(title="H04 Validation")

# Sequential, single-process learning only. No persistence or concurrency guarantee.
tasks: dict[int, TaskStored] = {}
next_id = 1


@app.get("/health")
def health():
    return {"status": "ok"}


def require_task(task_id: int) -> TaskStored:
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]


@app.post("/tasks", response_model=TaskPublic, status_code=201)
def create_task(payload: TaskCreate):
    global next_id
    record = TaskStored(id=next_id, **payload.model_dump())
    tasks[record.id] = record
    next_id += 1
    # Return all storage fields deliberately; response_model filters the HTTP body.
    return record.model_dump()


@app.get("/tasks", response_model=TaskPage)
def list_tasks(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    ordered = [tasks[key] for key in sorted(tasks)]
    return {
        "items": [record.model_dump() for record in ordered[offset:offset + limit]],
        "limit": limit,
        "offset": offset,
        "total": len(ordered),
    }


@app.get("/tasks/{task_id}", response_model=TaskPublic)
def read_task(task_id: int = Path(gt=0)):
    return require_task(task_id).model_dump()


@app.patch("/tasks/{task_id}", response_model=TaskPublic)
def patch_task(payload: TaskPatch, task_id: int = Path(gt=0)):
    current = require_task(task_id)
    changes = payload.model_dump(exclude_unset=True)
    candidate = current.model_dump()
    candidate.update(changes)
    # Validate the complete merged record before replacing anything in memory.
    updated = TaskStored.model_validate(candidate)
    tasks[task_id] = updated
    return updated.model_dump()


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int = Path(gt=0)):
    require_task(task_id)
    del tasks[task_id]
    return Response(status_code=204)
