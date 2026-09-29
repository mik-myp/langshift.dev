from collections.abc import Callable

from decorators import add_fee, double_result, register

operations: dict[str, Callable[[int], int]] = {}


@double_result
@add_fee(3)
def reversed_cost(minutes: int) -> int:
    return minutes


@add_fee(3)
@register(operations, "raw")
def registered_inside(minutes: int) -> int:
    return minutes


print(reversed_cost(4))
print(registered_inside(4), operations["raw"](4))
