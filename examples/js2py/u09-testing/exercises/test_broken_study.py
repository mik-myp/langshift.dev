from exercises.broken_study import pending_minutes


def test_completed_task_is_excluded():
    assert pending_minutes([{"minutes": 20, "done": True}]) == 0


def test_unfinished_task_is_included():
    assert pending_minutes([{"minutes": 35, "done": False}]) == 35
