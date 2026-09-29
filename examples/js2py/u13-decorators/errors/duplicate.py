from decorators import register

operations = {}


@register(operations, "cost")
def first(value):
    return value


@register(operations, "cost")
def second(value):
    return value
