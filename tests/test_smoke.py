"""冒烟测试：只验 import 与工具 schema 形状，不调 LLM、不跑 docker。"""

import pytest

import repopilot
from repopilot.tools import TOOLS, dispatch


def test_package_imports():
    assert repopilot.__version__


def test_tools_well_formed():
    assert {t["function"]["name"] for t in TOOLS} == {
        "read_file", "apply_patch", "run_tests", "write_file"}
    for t in TOOLS:
        assert t["type"] == "function"
        assert t["function"]["parameters"]["type"] == "object"
        assert isinstance(t["function"]["description"], str) and t["function"]["description"]


def test_unknown_tool_raises():
    with pytest.raises(KeyError):
        dispatch("nope", {}, repo=".")
