"""count_multiples 的行为测试。"""

from multiples import count_multiples


def test_ten_and_five():
    assert count_multiples(10, 5) == 2


def test_nine_and_three():
    assert count_multiples(9, 3) == 3


def test_zero():
    assert count_multiples(0, 3) == 0


def test_one_and_one():
    assert count_multiples(1, 1) == 1


def test_bad_k():
    assert count_multiples(10, 0) == 0
