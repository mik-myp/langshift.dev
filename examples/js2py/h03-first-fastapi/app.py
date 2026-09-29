from fastapi import FastAPI, HTTPException, Path, Query

app = FastAPI(title="H03 First FastAPI")

# Fixed, read-only examples; these are not a database or authenticated user data.
TASKS = {
    1: {"id": 1, "title": "Read HTTP", "minutes": 25, "done": False, "note": None},
    2: {"id": 2, "title": "Try curl", "minutes": 10, "done": True, "note": "local only"},
}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    ordered = [TASKS[task_id] for task_id in sorted(TASKS)]
    return {
        "items": ordered[offset:offset + limit],
        "limit": limit,
        "offset": offset,
        "total": len(ordered),
    }


@app.get("/tasks/{task_id}")
def read_task(task_id: int = Path(gt=0)):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    return TASKS[task_id]
