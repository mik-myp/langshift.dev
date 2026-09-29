from functools import wraps


def reject_above(limit: int):
    if type(limit) is not int or limit < 0:
        raise ValueError("limit must be a non-negative integer")

    def decorate(function):
        @wraps(function)
        def wrapped(value: int) -> int:
            if type(value) is not int or value < 0 or value > limit:
                raise ValueError("value outside permitted range")
            return function(value)

        return wrapped

    return decorate
