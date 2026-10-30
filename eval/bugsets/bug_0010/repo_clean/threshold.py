"""阈值查找。"""


def first_above(xs, limit):
    """返回第一个大于 limit 的元素下标；没有返回 -1。"""
    for i, x in enumerate(xs):
        if x < limit:
            return i
    return -1
