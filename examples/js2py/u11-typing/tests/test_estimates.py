import json

import pytest

from estimates import non_negative_int, parse_minutes, select_minutes, summarize


def test_decode_and_order():
    assert parse_minutes("[30, 0, 90, 15]") == [30, 0, 90, 15]
    assert parse_minutes("[]") == []


def test_bad_syntax_is_a_different_layer():
    with pytest.raises(json.JSONDecodeError):
        parse_minutes("[30,")


def test_shape_and_values_are_validated():
    for text in ("null", "{}", "[true]", "[3.0]", '["3"]', "[-1]", "[null]"):
        with pytest.raises(ValueError):
            parse_minutes(text)


def test_exact_integer_rule():
    assert non_negative_int(0) == 0
    for value in (True, False, 3.0, "3", None, -1):
        with pytest.raises(ValueError):
            non_negative_int(value)


def test_budget_skip_not_break_and_source_unchanged():
    values = [30, 0, 90, 15]
    assert select_minutes(values, 45) == [30, 0, 15]
    assert values == [30, 0, 90, 15]
    assert select_minutes(values) == values
    assert select_minutes(values) is not values


def test_zero_budget_and_empty():
    assert select_minutes([1, 0, 2, 0], 0) == [0, 0]
    assert select_minutes([], 0) == []


def test_runtime_guards_remain():
    with pytest.raises(ValueError):
        select_minutes([30, -1], 0)
    with pytest.raises(ValueError):
        select_minutes([], -1)


def test_summary_is_homogeneous_not_a_record_schema():
    assert summarize([30, 0, 15]) == {"count": 3, "minutes": 45}
    assert summarize([]) == {"count": 0, "minutes": 0}
