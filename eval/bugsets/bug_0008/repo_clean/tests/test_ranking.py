"""top_k 的边界测试。"""

from ranking import top_k


def test_top_two():
    assert top_k([1, 5, 3], 2) == [5, 3]


def test_k_zero():
    assert top_k([1, 5, 3], 0) == []


def test_k_negative():
    assert top_k([1, 5, 3], -1) == []


def test_k_too_large():
    assert top_k([2, 1], 5) == [2, 1]


def test_empty():
    assert top_k([], 2) == []


def test_k_negative_two():
    assert top_k([1, 5, 3], -2) == []
