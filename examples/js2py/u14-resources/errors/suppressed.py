from contextlib import contextmanager


@contextmanager
def wrong_boundary():
    try:
        yield
    except ValueError:
        print("hidden")  # Wrong policy here: no re-raise, so the caller continues.


with wrong_boundary():
    raise ValueError("save failed")
print("continued")
