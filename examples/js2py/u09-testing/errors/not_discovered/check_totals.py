from study import pending_minutes


def test_empty():
    assert pending_minutes([]) == 0
