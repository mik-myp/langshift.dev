from fastapi import APIRouter, Depends, HTTPException, Path, Response

from task_api.dependencies import Page, RequestTrace, get_page, get_store, request_trace
from task_api.models import TaskCreate, TaskPage, TaskPatch, TaskPublic, TaskStored
from task_api.store import MemoryStore

router = APIRouter(prefix="/tasks", tags=["tasks"])


def require_task(store: MemoryStore, task_id: int) -> TaskStored:
    record = store.get(task_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return record


@router.post("", response_model=TaskPublic, status_code=201)
def create_task(
    payload: TaskCreate,
    store: MemoryStore = Depends(get_store),
    trace: RequestTrace = Depends(request_trace, scope="function"),
):
    trace.mark("create_task")
    return store.create(payload).model_dump()


@router.get("", response_model=TaskPage)
def list_tasks(
    page: Page = Depends(get_page),
    store: MemoryStore = Depends(get_store),
):
    ordered = store.ordered()
    return {
        "items": [record.model_dump() for record in ordered[page.offset:page.offset + page.limit]],
        "limit": page.limit,
        "offset": page.offset,
        "total": len(ordered),
    }


@router.get("/{task_id}", response_model=TaskPublic)
def read_task(
    task_id: int = Path(gt=0),
    store: MemoryStore = Depends(get_store),
):
    return require_task(store, task_id).model_dump()


@router.patch("/{task_id}", response_model=TaskPublic)
def patch_task(
    payload: TaskPatch,
    task_id: int = Path(gt=0),
    store: MemoryStore = Depends(get_store),
):
    current = require_task(store, task_id)
    return store.patch(current, payload).model_dump()


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int = Path(gt=0),
    store: MemoryStore = Depends(get_store),
):
    require_task(store, task_id)
    store.delete(task_id)
    return Response(status_code=204)
