import pytest

from solutions.work_log import WorkLog


def test_owned_inputs_and_independent_instances():
    source = [10, 0]
    first = WorkLog("Read", source)
    second = WorkLog("Write")
    source.append(999)
    first.add(5)
    assert first.entries == [10, 0, 5]
    assert first.total_minutes() == 15
    assert second.total_minutes() == 0


def test_failure_does_not_append():
    log = WorkLog("Read", [10])
    for value in (-1, True, 1.5, "5"):
        with pytest.raises(ValueError):
            log.add(value)
    assert log.entries == [10]
    with pytest.raises(ValueError):
        WorkLog(" ")
