"""带默认值的列表取值。"""


def safe_get(xs, i, default=None):
    """取 xs[i]；下标越界（含负数）时返回 default。"""
    if i >= len(xs):
        return default
    return xs[i]
