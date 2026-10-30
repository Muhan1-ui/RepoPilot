"""序列小工具。"""


def take_last(xs, n):
    """返回列表最后 n 个元素；n<=0 时返回空列表。"""
    return xs[-n - 1:]
