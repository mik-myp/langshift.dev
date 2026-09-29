import pytest
from task_app.app import initial_tasks
from task_app.rules import complete_title, summarize
from task_app.validation import validate_tasks


def test_normal_completion_and_summary():
    result, changed = complete_title(initial_tasks(), "Read")
    assert changed == 1
    assert result[0]["done"] is True
    assert summarize(result) == {"count": 3, "pending_minutes": 35}


def test_zero_empty_and_no_matching_title():
    assert summarize([]) == {"count": 0, "pending_minutes": 0}
    assert complete_title([], "Read") == ([], 0)
    tasks = [{"title": "Zero", "minutes": 0, "done": False}]
    result, changed = complete_title(tasks, "Absent")
    assert changed == 0 and result == tasks
    assert summarize(result)["pending_minutes"] == 0


def test_every_duplicate_matches_but_only_new_changes_count():
    tasks = [
        {"title": "Read", "minutes": 1, "done": False},
        {"title": "Read", "minutes": 2, "done": True},
        {"title": "Read", "minutes": 3, "done": False},
    ]
    result, changed = complete_title(tasks, "Read")
    assert changed == 2
    assert summarize(result)["pending_minutes"] == 0
    repeated, changed_again = complete_title(result, "Read")
    assert changed_again == 0 and repeated == result


def test_input_and_returned_records_do_not_share_mutation():
    source = initial_tasks()
    result, changed = complete_title(source, "Read")
    assert changed == 1 and source == initial_tasks()
    result[1]["minutes"] = 999
    assert source[1]["minutes"] == 35


def test_strict_shape_and_types():
    with pytest.raises(ValueError):
        validate_tasks({"tasks": []})
    with pytest.raises(ValueError):
        validate_tasks([{"title": "Read", "minutes": True, "done": False}])
    with pytest.raises(ValueError):
        validate_tasks([{"title": "Read", "minutes": 20, "done": 0}])
    with pytest.raises(ValueError):
        validate_tasks([{"title": "Read", "minutes": -1, "done": False}])
    with pytest.raises(ValueError):
        validate_tasks([{"title": "Read", "minutes": "20", "done": False}])
    with pytest.raises(ValueError):
        validate_tasks([{"title": "Read", "minutes": 20, "done": False, "extra": 1}])


def test_title_spelling_and_invalid_selection():
    tasks = [{"title": " Read ", "minutes": 20, "done": False}]
    result, changed = complete_title(tasks, "Read")
    assert changed == 0 and result[0]["title"] == " Read "
    with pytest.raises(ValueError):
        complete_title(tasks, "   ")
    with pytest.raises(ValueError):
        complete_title(tasks, None)
