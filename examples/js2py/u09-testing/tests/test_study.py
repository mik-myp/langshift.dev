import pytest
from study import pending_minutes


def test_only_unfinished_minutes_count():
    tasks = [{"minutes": 20, "done": True}, {"minutes": 35, "done": False}]
    assert pending_minutes(tasks) == 35


def test_empty_input_is_zero():
    assert pending_minutes([]) == 0


def test_zero_is_a_valid_estimate():
    assert pending_minutes([{"minutes": 0, "done": False}]) == 0


def test_input_and_repeated_calls_are_unchanged():
    tasks = [{"minutes": 20, "done": False}]
    assert pending_minutes(tasks) == 20
    assert pending_minutes(tasks) == 20
    assert tasks == [{"minutes": 20, "done": False}]


def test_bool_is_not_an_ordinary_minute_count():
    with pytest.raises(ValueError) as caught:
        pending_minutes([{"minutes": True, "done": False}])
    assert str(caught.value) == "minutes must be a nonnegative int"


def test_numeric_text_is_not_accepted():
    with pytest.raises(ValueError):
        pending_minutes([{"minutes": "20", "done": False}])
