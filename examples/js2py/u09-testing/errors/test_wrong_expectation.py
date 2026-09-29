from study import pending_minutes


def test_wrong_expectation():
    result = pending_minutes([{"minutes": 20, "done": False}])
    assert result == 99
