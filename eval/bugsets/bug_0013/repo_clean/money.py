"""金额解析与累加。"""


def parse_amount(text: str) -> float:
    """把金额字符串解析成数值。"""
    return float(text)


def sum_amounts(texts: list[str]) -> float:
    """累加多个金额字符串。"""
    total = 0.0
    for text in texts:
        total += parse_amount(text)
    return total


def to_cents(amount) -> int:
    """把元换算成整数分（四舍五入）。"""
    return int(amount * 100 + 0.5)
