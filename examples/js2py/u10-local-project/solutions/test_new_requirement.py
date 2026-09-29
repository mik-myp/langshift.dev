import pytest

from solutions.new_requirement import plan_within_budget


def test_order_skip_and_later_fit():
    tasks = [
        {"title": "Large", "minutes": 50, "done": False},
        {"title": "Fit", "minutes": 20, "done": False},
        {"title": "Zero", "minutes": 0, "done": False},
        {"title": "Done", "minutes": 1, "done": True},
    ]
    selected, used = plan_within_budget(tasks, 20)
    assert [task["title"] for task in selected] == ["Fit", "Zero"]
    assert used == 20
    selected[0]["done"] = True
    assert tasks[1]["done"] is False


def test_empty_zero_and_rejections():
    assert plan_within_budget([], 0) == ([], 0)
    with pytest.raises(ValueError):
        plan_within_budget([], True)
    with pytest.raises(ValueError):
        plan_within_budget([], -1)
    with pytest.raises(ValueError):
        plan_within_budget([None], 20)
