# mypy rejects this call; Python still executes it without validating annotations.
def double(value: int) -> int:
    return value * 2


print(double("3"))
