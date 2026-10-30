"""解析 key=value 形式的配置行。"""


def parse_line(line: str) -> tuple[str, str]:
    """把一行配置解析成 (key, value)；空行和注释行返回 ("", "")。"""
    line = line.strip()
    if not line or line.startswith("#"):
        return "", ""
    if "=" not in line:
        raise ValueError(f"bad config line: {line!r}")
    key, _, value = line.partition("=")
    return key.lstrip(), value.strip()
