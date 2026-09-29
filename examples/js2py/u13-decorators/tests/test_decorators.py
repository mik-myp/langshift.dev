import pytest

from decorators import add_fee, double_result, register


@pytest.mark.parametrize("value, expected", [(0, 0), (4, 8), (15, 30)])
def test_wrapper(value, expected):
    def identity(minutes):
        return minutes

    decorated = double_result(identity)
    assert decorated(value) == expected
    assert decorated is not identity
    assert decorated.__name__ == "identity"


def test_factory_does_not_call_business_function():
    calls = []

    def operation(value):
        calls.append(value)
        return value

    decorated = add_fee(3)(operation)
    assert calls == []
    assert decorated(4) == 7
    assert decorated(5) == 8
    assert calls == [4, 5]


def test_closures_keep_independent_configuration():
    def identity(value):
        return value

    assert add_fee(3)(identity)(4) == 7
    assert add_fee(10)(identity)(4) == 14


def test_registration_keeps_identity_and_rejects_collision():
    registry = {}

    def identity(value):
        return value

    assert register(registry, "first")(identity) is identity
    assert registry["first"](4) == 4
    with pytest.raises(ValueError):
        register(registry, "first")(identity)


def test_order_changes_behavior():
    def identity(value):
        return value

    assert add_fee(3)(double_result(identity))(4) == 11
    assert double_result(add_fee(3)(identity))(4) == 14


def test_wrappers_do_not_swallow_errors():
    def broken(value):
        raise ValueError("business failure")

    with pytest.raises(ValueError, match="business failure"):
        double_result(broken)(4)
