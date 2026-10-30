"""get_score 的行为测试。"""

from scores import get_score


def test_present():
    assert get_score({"alice": 90}, "alice") == 90


def test_missing_returns_none():
    assert get_score({"alice": 90}, "bob") is None


def test_empty_dict_returns_none():
    assert get_score({}, "alice") is None


def test_zero_score_is_not_none():
    assert get_score({"alice": 0}, "alice") == 0
