"""first_above 的行为测试。"""

from threshold import first_above


def test_found_in_middle():
    assert first_above([1, 5, 2], 3) == 1


def test_none_above():
    assert first_above([1, 2], 3) == -1


def test_first_element():
    assert first_above([4, 1], 3) == 0


def test_empty():
    assert first_above([], 3) == -1


def test_negative_limit():
    assert first_above([-5, 10], 0) == 1
