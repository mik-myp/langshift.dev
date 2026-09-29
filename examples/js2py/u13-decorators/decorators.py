from collections.abc import Callable
from functools import wraps


def double_result(function: Callable[[int], int]) -> Callable[[int], int]:
    @wraps(function)
    def wrapped(value: int) -> int:
        return function(value) * 2

    return wrapped


def add_fee(fee: int):
    if type(fee) is not int or fee < 0:
        raise ValueError("fee must be a non-negative integer")

    def decorate(function: Callable[[int], int]) -> Callable[[int], int]:
        @wraps(function)
        def wrapped(value: int) -> int:
            return function(value) + fee

        return wrapped

    return decorate


def register(registry: dict[str, Callable[[int], int]], name: str):
    # Return annotation intentionally omitted to keep this repeated shape readable.
    def decorate(function: Callable[[int], int]) -> Callable[[int], int]:
        if name in registry:
            raise ValueError("duplicate operation: " + name)
        registry[name] = function
        return function

    return decorate
