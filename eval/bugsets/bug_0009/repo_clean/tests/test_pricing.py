"""total_price 的行为测试。"""

from pricing import total_price


def test_two_items():
    assert total_price("2.5", "4") == 10.0


def test_integer_strings():
    assert total_price("3", "3") == 9.0


def test_zero_qty():
    assert total_price("9.9", "0") == 0.0


def test_decimal_qty():
    assert total_price("10", "2.5") == 25.0
