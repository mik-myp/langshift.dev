from solutions.summary import summarize
from task_api.models import TaskCreate, TaskPatch
from task_api.store import MemoryStore


def test_empty_summary():
    assert summarize(MemoryStore()) == {"total": 0, "done": 0, "minutes": 0}


def test_summary_tracks_changes():
    store = MemoryStore()
    first = store.create(TaskCreate(title="Read", minutes=30))
    second = store.create(TaskCreate(title="Write", minutes=0, done=True))
    assert summarize(store) == {"total": 2, "done": 1, "minutes": 30}
    store.patch(first, TaskPatch(done=True, minutes=5))
    assert summarize(store) == {"total": 2, "done": 2, "minutes": 5}
    store.delete(second.id)
    assert summarize(store) == {"total": 1, "done": 1, "minutes": 5}
