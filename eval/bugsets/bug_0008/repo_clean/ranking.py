"""排行榜。"""


def top_k(xs, k):
    """返回最大的 k 个元素（降序）；k<=0 返回 []，k 超过长度返回全部。"""
    return sorted(xs, reverse=True)[:k]
