# Equivalent expansion for this example's independent, side-effect-free factories.
from collections.abc import Callable

from decorators import add_fee, double_result, register

operations: dict[str, Callable[[int], int]] = {}
registration = register(operations, "cost")
fee_decoration = add_fee(3)


def cost(minutes: int) -> int:
    return minutes


cost = registration(fee_decoration(double_result(cost)))
print(cost(4), operations["cost"](4))
