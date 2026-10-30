"""to_fahrenheit 的行为测试。"""

from temperature import to_fahrenheit


def test_freezing():
    assert to_fahrenheit(0) == 32


def test_boiling():
    assert to_fahrenheit(100) == 212


def test_body_temperature():
    assert to_fahrenheit(37) == 98.6


def test_negative_forty():
    assert to_fahrenheit(-40) == -40.0


def test_float_input():
    assert round(to_fahrenheit(36.6), 2) == 97.88
