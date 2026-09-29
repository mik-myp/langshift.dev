import json


def non_negative_int(value: object) -> int:
    if type(value) is not int:
        raise ValueError("minutes must be an integer, not bool or text")
    if value < 0:
        raise ValueError("minutes must not be negative")
    return value


def parse_minutes(text: str) -> list[int]:
    # JSON decoding returns dynamically shaped data, not a trusted list[int].
    raw: object = json.loads(text)
    if not isinstance(raw, list):
        raise ValueError("minutes must be a JSON array")
    result: list[int] = []
    for value in raw:
        result.append(non_negative_int(value))
    return result


def select_minutes(values: list[int], budget: int | None = None) -> list[int]:
    if budget is not None:
        non_negative_int(budget)
    selected: list[int] = []
    used = 0
    for value in values:
        non_negative_int(value)
        if budget is None or used + value <= budget:
            selected.append(value)
            used += value
    return selected


def summarize(values: list[int]) -> dict[str, int]:
    for value in values:
        non_negative_int(value)
    return {"count": len(values), "minutes": sum(values)}
