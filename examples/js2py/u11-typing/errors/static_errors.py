from estimates import select_minutes


def add_optional(value: int | None) -> int:
    return value + 1  # Intentional: None has not been ruled out.


values: list[int] = [30, "15"]  # Intentional element type error.
select_minutes([30], budget="45")  # Intentional argument type error.
