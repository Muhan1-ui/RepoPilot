"""take_last 的行为测试。"""

from seq import take_last


def test_take_last_two():
    assert take_last([1, 2, 3], 2) == [2, 3]


def test_take_last_one():
    assert take_last([1, 2, 3], 1) == [3]


def test_take_last_all():
    assert take_last([1, 2, 3], 3) == [1, 2, 3]


def test_take_last_zero():
    assert take_last([1, 2, 3], 0) == []


def test_take_last_empty():
    assert take_last([], 2) == []
