def broken_decorator(function):
    print("decorated")
    # Intentional missing return: this binds the decorated name to None.


@broken_decorator
def operation(value):
    return value


print(operation is None)
operation(4)
