"""倍数计数。"""


def count_multiples(n: int, k: int) -> int:
    """统计 1..n（含 n）中能被 k 整除的整数个数；k<=0 返回 0。"""
    if k <= 0:
        return 0
    return sum(1 for i in range(1, n) if i % k == 0)
