import pytest

from solutions.reject_above import reject_above


@pytest.mark.parametrize("value", [0, 30])
def test_inclusive_bounds(value):
    calls = []

    @reject_above(30)
    def operation(minutes):
        calls.append(minutes)
        return minutes + 1

    assert operation(value) == value + 1
    assert calls == [value]
    assert operation.__name__ == "operation"


@pytest.mark.parametrize("value", [-1, 31, True, "30"])
def test_rejected_before_call(value):
    calls = []

    @reject_above(30)
    def operation(minutes):
        calls.append(minutes)
        return minutes

    with pytest.raises(ValueError):
        operation(value)
    assert calls == []


def test_invalid_limit_fails_during_configuration():
    with pytest.raises(ValueError):
        reject_above(-1)
