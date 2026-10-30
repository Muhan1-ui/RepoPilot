"""基础统计函数。"""


def mean(xs: list[float]) -> float:
    """返回算术平均值。"""
    if not xs:
        raise ValueError("empty list")
    return sum(xs) / len(xs)


def median(xs: list[float]) -> float:
    """返回中位数。"""
    if not xs:
        raise ValueError("empty list")
    ordered = sorted(xs)
    return ordered[len(ordered) // 2]
