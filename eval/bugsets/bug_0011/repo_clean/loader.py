"""把配置文本装载成字典。"""

from parser import parse_line

DEFAULTS = {"host": "localhost", "port": "80", "timeout": "30"}


def load(text: str) -> dict[str, str]:
    """解析整段配置文本，未知键抛 ValueError。"""
    config = dict(DEFAULTS)
    for line in text.splitlines():
        key, value = parse_line(line)
        if not key:
            continue
        if key not in DEFAULTS:
            raise ValueError(f"unknown config key: {key.strip()}")
        config[key] = value
    return config


def get(config: dict[str, str], name: str) -> str:
    """取配置值；缺失时抛 KeyError。"""
    if name not in config:
        raise KeyError(name)
    return config[name]
