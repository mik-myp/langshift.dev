from fastapi import APIRouter, Depends
from pydantic import BaseModel

from task_api.dependencies import get_store
from task_api.main import create_app
from task_api.store import MemoryStore

router = APIRouter()


class Summary(BaseModel):
    total: int
    done: int
    minutes: int


def summarize(store: MemoryStore) -> dict[str, int]:
    records = store.ordered()
    return {
        "total": len(records),
        "done": sum(1 for record in records if record.done),
        "minutes": sum(record.minutes for record in records),
    }


@router.get("/summary", response_model=Summary)
def read_summary(store: MemoryStore = Depends(get_store)):
    return summarize(store)


def create_summary_app():
    app = create_app()
    app.include_router(router)
    return app
