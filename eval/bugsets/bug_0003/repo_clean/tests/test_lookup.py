"""safe_get 的边界测试。"""

from lookup import safe_get


def test_in_range():
    assert safe_get([10, 20, 30], 1) == 20


def test_out_of_range_returns_default():
    assert safe_get([10, 20, 30], 5, "x") == "x"


def test_negative_index_returns_default():
    assert safe_get([10, 20, 30], -1, "x") == "x"


def test_empty_list_returns_default():
    assert safe_get([], 0, "x") == "x"


def test_empty_list_negative_returns_default():
    assert safe_get([], -1, "x") == "x"
