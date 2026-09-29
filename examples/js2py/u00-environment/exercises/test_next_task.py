import pytest

from next_task import next_task_title


@pytest.mark.parametrize(
    ("tasks", "expected"),
    [
        ([], "No pending tasks"),
        ([{"title": "Finished", "done": True}], "No pending tasks"),
        ([{"title": "First", "done": False}], "First"),
        (
            [
                {"title": "Finished", "done": True},
                {"title": "Next", "done": False},
                {"title": "Later", "done": False},
            ],
            "Next",
        ),
    ],
)
def test_next_task_title(tasks, expected):
    original = [task.copy() for task in tasks]
    assert next_task_title(tasks) == expected
    assert tasks == original
