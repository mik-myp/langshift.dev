from estimates import non_negative_int


def first_over(values: list[int], limit: int) -> int | None:
    non_negative_int(limit)
    for value in values:
        non_negative_int(value)
    for value in values:
        if value > limit:
            return value
    return None
