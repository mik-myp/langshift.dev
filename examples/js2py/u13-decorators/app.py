from collections.abc import Callable

from decorators import add_fee, double_result, register

operations: dict[str, Callable[[int], int]] = {}


@register(operations, "cost")
@add_fee(3)
@double_result
def cost(minutes: int) -> int:
    """Return a demonstration cost, not real currency arithmetic."""
    return minutes


def main() -> None:
    print(sorted(operations))
    print(cost(4), operations["cost"](4))
    print(cost.__name__)
    print(cost is operations["cost"])


if __name__ == "__main__":
    main()
