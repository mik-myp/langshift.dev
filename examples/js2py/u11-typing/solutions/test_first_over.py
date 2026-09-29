import pytest

from solutions.first_over import first_over


def test_first_match_and_no_match():
    values = [0, 30, 90, 45]
    assert first_over(values, 30) == 90
    assert first_over(values, 90) is None
    assert first_over([], 0) is None
    assert values == [0, 30, 90, 45]


def test_validation_includes_later_elements():
    with pytest.raises(ValueError):
        first_over([90, -1], 30)
    with pytest.raises(ValueError):
        first_over([1], -1)
