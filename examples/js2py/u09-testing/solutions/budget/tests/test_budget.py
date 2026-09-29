import pytest
from budget import remaining_budget


def test_normal_remaining():
    assert remaining_budget(20, [5, 8]) == 7


def test_empty_spending():
    assert remaining_budget(20, []) == 20


def test_exact_boundary():
    assert remaining_budget(20, [5, 15]) == 0


def test_overspending_is_clamped():
    assert remaining_budget(20, [30]) == 0


def test_zero_budget_and_zero_spending():
    assert remaining_budget(0, [0]) == 0


def test_invalid_budget():
    with pytest.raises(ValueError):
        remaining_budget(True, [])
    with pytest.raises(ValueError):
        remaining_budget(-1, [])


def test_wrong_root():
    with pytest.raises(ValueError):
        remaining_budget(20, (5,))


def test_invalid_spending_items():
    with pytest.raises(ValueError):
        remaining_budget(20, [True])
    with pytest.raises(ValueError):
        remaining_budget(20, ["5"])
    with pytest.raises(ValueError):
        remaining_budget(20, [1.5])
    with pytest.raises(ValueError):
        remaining_budget(20, [-1])


def test_input_and_repeat_are_independent():
    spent = [5, 8]
    assert remaining_budget(20, spent) == 7
    assert remaining_budget(20, spent) == 7
    assert spent == [5, 8]
