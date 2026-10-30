"""温度转换。"""


def to_fahrenheit(celsius: float) -> float:
    """摄氏转华氏：C * 9 / 5 + 32，返回浮点数。"""
    return celsius * 9 // 5 + 32
