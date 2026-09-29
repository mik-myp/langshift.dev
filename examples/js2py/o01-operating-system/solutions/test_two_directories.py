from solutions.two_directories import observe


def test_two_explicit_roots_are_independent_of_the_working_directory():
    assert observe() == [2, 1]
