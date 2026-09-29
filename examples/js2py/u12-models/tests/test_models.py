import pytest

from models import Estimate, Plan, RawEstimate, Task, UrgentTask


def test_bound_method_and_explicit_instance_agree():
    task = Task("Read", 30)
    assert task.label() == Task.label(task) == "Read"


def test_repeated_transition_and_separate_instances():
    first = Task("Read", 30)
    second = Task("Read", 30)
    assert first.mark_done() is True
    assert first.mark_done() is False
    assert first.remaining_minutes() == 0
    assert second.remaining_minutes() == 30


def test_constructor_validation():
    for value in (-1, True, 1.5, "30"):
        with pytest.raises(ValueError):
            Task("Read", value)
    with pytest.raises(ValueError):
        Task(" ", 30)
    with pytest.raises(ValueError):
        Task("Read", 30, done=1)


def test_composition_copies_list_not_tasks():
    task = Task("Read", 30)
    source = [task]
    plan = Plan(source)
    source.clear()
    assert plan.remaining_minutes() == 30
    task.mark_done()
    assert plan.remaining_minutes() == 0


def test_inherited_behavior_and_overridden_label():
    task = UrgentTask("Write", 15)
    assert isinstance(task, Task)
    assert task.label() == "! Write"
    assert task.mark_done() is True
    assert task.remaining_minutes() == 0


def test_dataclass_equality_is_not_identity():
    first = Estimate("Read", 30)
    second = Estimate("Read", 30)
    assert first == second
    assert first is not second
    first.tags.append("python")
    assert first != second
    assert second.tags == []


def test_dataclass_explicit_input_list_is_copied():
    tags = ["python"]
    record = Estimate("Read", 30, tags)
    tags.append("changed")
    assert record.tags == ["python"]


def test_dataclass_validation_is_explicit():
    with pytest.raises(ValueError):
        Estimate("Read", -1)
    with pytest.raises(ValueError):
        Estimate("Read", 30, [1])
    raw = RawEstimate("Read", "30")
    assert raw.minutes == "30"


def test_public_mutation_is_not_a_validation_boundary():
    task = Task("Read", 30)
    task.minutes = -1
    assert task.remaining_minutes() == -1
