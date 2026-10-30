"""first_negative 的行为测试。"""

from search import first_negative


def test_found_in_middle():
    assert first_negative([1, -2, 3]) == 1


def test_no_negative():
    assert first_negative([1, 2, 3]) == -1


def test_first_element():
    assert first_negative([-5, 1]) == 0


def test_empty():
    assert first_negative([]) == -1


def test_zeros_are_not_negative():
    assert first_negative([0, 0]) == -1
