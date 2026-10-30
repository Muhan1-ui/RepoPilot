"""金额解析与累加测试。"""

from decimal import Decimal

import pytest

from money import parse_amount, sum_amounts, to_cents


def test_parse_returns_decimal():
    assert isinstance(parse_amount("0.10"), Decimal)


def test_parse_is_exact():
    assert parse_amount("0.1") == Decimal("0.1")


def test_parse_keeps_scale():
    assert str(parse_amount("1.50")) == "1.50"


def test_parse_rejects_negative():
    with pytest.raises(ValueError):
        parse_amount("-1")


def test_parse_rejects_garbage():
    with pytest.raises(ValueError):
        parse_amount("abc")


def test_sum_is_exact():
    assert sum_amounts(["0.10", "0.20"]) == Decimal("0.30")


def test_sum_empty():
    assert sum_amounts([]) == Decimal("0")


def test_to_cents_rounds_half_up():
    assert to_cents(parse_amount("1.005")) == 101
