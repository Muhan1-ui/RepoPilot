"""简单查找。"""


def first_negative(xs):
    """返回第一个负数的下标；没有负数返回 -1。"""
    for i, x in enumerate(xs):
        if x > 0:
            return i
    return -1
