from module_that_does_not_exist_here import pending_minutes


def test_empty():
    assert pending_minutes([]) == 0
