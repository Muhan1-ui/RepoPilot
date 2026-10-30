"""parse_line 的行为测试。"""

import pytest

from parser import parse_line


def test_parse_simple():
    assert parse_line("host=example.com") == ("host", "example.com")


def test_parse_spaces_around_equals():
    assert parse_line("  port = 8080  ") == ("port", "8080")


def test_key_has_no_trailing_whitespace():
    key, _ = parse_line("timeout = 5")
    assert key == "timeout"
    assert not key.endswith(" ")


def test_value_keeps_inner_spaces():
    assert parse_line("greeting = hello world") == ("greeting", "hello world")


def test_blank_and_comment_lines():
    assert parse_line("") == ("", "")
    assert parse_line("   # note") == ("", "")


def test_missing_equals_raises():
    with pytest.raises(ValueError):
        parse_line("just-a-word")
