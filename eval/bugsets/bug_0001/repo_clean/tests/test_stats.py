"""stats 的行为测试。"""

from stats import mean, median


def test_mean():
    assert mean([1, 2, 3]) == 2


def test_median_odd():
    assert median([3, 1, 2]) == 2
    assert median([5]) == 5


def test_median_even():
    assert median([1, 2, 3, 4]) == 2.5


def test_median_two():
    assert median([10, 20]) == 15
