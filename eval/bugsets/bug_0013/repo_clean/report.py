"""把金额汇总渲染成报表。"""

from money import sum_amounts


def total_cents(texts: list[str]) -> int:
    """返回合计金额（分）。"""
    return int(sum_amounts(texts) * 100 + 0.5)


def render(texts: list[str]) -> str:
    """渲染成 '合计：¥x.xx（N 分）'。"""
    cents = total_cents(texts)
    return f"合计：¥{cents // 100}.{cents % 100:02d}（{cents} 分）"
