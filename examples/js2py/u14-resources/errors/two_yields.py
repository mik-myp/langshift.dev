from contextlib import contextmanager


@contextmanager
def wrong_resource():
    yield "first"
    yield "second"  # Intentional: a contextmanager must yield exactly once.


with wrong_resource() as value:
    print(value)
