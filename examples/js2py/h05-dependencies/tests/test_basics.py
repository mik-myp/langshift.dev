import pytest
from pydantic import ValidationError

from task_api.config import load_settings
from task_api.main import create_app
from task_api.models import TaskCreate, TaskPatch
from task_api.store import MemoryStore


def test_default_settings():
    assert load_settings({"TASKS_APP_NAME": "  Learning  "}).app_name == "Learning"
    assert load_settings({"TASKS_APP_NAME": "Learning"}).max_page_size == 100


@pytest.mark.parametrize("name", [None, "", "  "])
def test_missing_name(name):
    environ = {} if name is None else {"TASKS_APP_NAME": name}
    with pytest.raises(ValueError, match="TASKS_APP_NAME is required"):
        load_settings(environ)


@pytest.mark.parametrize("value", ["19", "101", "3.0", "true", "", " 20", "２０"])
def test_bad_limit_does_not_echo_value(value):
    with pytest.raises(ValueError) as captured:
        load_settings({"TASKS_APP_NAME": "Learning", "TASKS_MAX_PAGE_SIZE": value})
    assert str(captured.value) == "TASKS_MAX_PAGE_SIZE must be an integer from 20 to 100"


def test_custom_limit():
    assert load_settings({"TASKS_APP_NAME": "Learning", "TASKS_MAX_PAGE_SIZE": "20"}).max_page_size == 20


def test_factory_owns_state():
    settings = load_settings({"TASKS_APP_NAME": "Test"})
    left, right = create_app(settings), create_app(settings)
    left.state.store.create(TaskCreate(title="Read", minutes=3))
    assert len(left.state.store.ordered()) == 1
    assert right.state.store.ordered() == []
    assert right.state.store.next_id == 1


def test_patch_states_without_http():
    store = MemoryStore()
    task = store.create(TaskCreate(title="  Read  ", minutes=0, note="keep"))
    assert store.patch(task, TaskPatch()).note == "keep"
    task = store.patch(task, TaskPatch(note="replace"))
    assert task.note == "replace"
    assert store.patch(task, TaskPatch(note=None)).note is None
    assert task.title == "  Read  "


def test_invalid_candidate_cannot_mutate_store():
    store = MemoryStore()
    record = store.create(TaskCreate(title="Read", minutes=3))
    with pytest.raises(ValidationError):
        patch = TaskPatch(title="Changed", minutes=True)
        store.patch(record, patch)
    assert store.get(record.id).title == "Read"
