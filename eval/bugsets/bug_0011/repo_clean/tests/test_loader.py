"""load/get 的行为测试。"""

import pytest

from loader import DEFAULTS, get, load


def test_empty_text_returns_defaults():
    assert load("") == DEFAULTS


def test_override_default():
    assert load("host = example.com")["host"] == "example.com"


def test_multiple_entries():
    cfg = load("port = 8080\ntimeout = 5")
    assert cfg["port"] == "8080"
    assert cfg["timeout"] == "5"


def test_comments_are_ignored():
    assert load("# note\nhost = h")["host"] == "h"


def test_unknown_key_raises():
    with pytest.raises(ValueError):
        load("bogus = 1")


def test_get_returns_value_and_raises_when_missing():
    cfg = {"port": "8080"}
    assert get(cfg, "port") == "8080"
    with pytest.raises(KeyError):
        get(cfg, "host")
