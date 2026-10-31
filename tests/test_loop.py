"""Loop 自测：MockModel 从红到绿 + max_steps 熔断。"""

import json
import sys

from repopilot.llm import MockModel
from repopilot.loop import run_task

PATCH = ("--- a/calc.py\n+++ b/calc.py\n@@ -1,2 +1,2 @@\n"
         " def add(a, b):\n-    return a - b\n+    return a + b\n")


def _setup(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    (repo / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n", encoding="utf-8")
    script = tmp_path / "script.json"
    script.write_text(json.dumps([
        {"name": "read_file", "args": {"path": "calc.py"}},
        {"name": "apply_patch", "args": {"patch": PATCH}},
        {"name": "run_tests", "args": {}}]), encoding="utf-8")
    return repo, script


def test_red_to_green(tmp_path):
    repo, script = _setup(tmp_path)
    trace = tmp_path / "trace.jsonl"
    res = run_task(repo, MockModel(script), f"{sys.executable} -m pytest -q",
                   max_steps=5, trace_path=trace)
    assert (res["ok"], res["reason"], res["steps"]) == (True, "tests_passed", 3)
    lines = [json.loads(x) for x in trace.read_text(encoding="utf-8").splitlines()]
    assert [x["tool"] for x in lines] == ["read_file", "apply_patch", "run_tests",
                                          "verify_rerun"]
    assert lines[-1]["verify_rerun"] == "passed"
    assert all(len(x["args_digest"]) <= 200 for x in lines)


def test_false_positive_blocked_when_model_cmd_passes_but_full_suite_fails(tmp_path):
    """模型用“只跑绿的那一个文件”拿到 exit_code=0，全量复核必须把它拦下。"""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "test_ok.py").write_text(
        "def test_ok():\n    assert True\n", encoding="utf-8")
    (repo / "test_bad.py").write_text(
        "def test_bad():\n    assert False\n", encoding="utf-8")
    script = tmp_path / "script.json"
    script.write_text(json.dumps([
        {"name": "run_tests",
         "args": {"cmd": f"{sys.executable} -m pytest -q test_ok.py"}}]), encoding="utf-8")
    trace = tmp_path / "trace.jsonl"

    res = run_task(repo, MockModel(script), f"{sys.executable} -m pytest -q",
                   max_steps=3, trace_path=trace)

    assert res["ok"] is False
    assert res["reason"] == "false_positive_blocked"
    assert "模型命令返回 0 但全量复核失败" in res["detail"]
    records = [json.loads(x) for x in trace.read_text(encoding="utf-8").splitlines()]
    verify = [r for r in records if r["tool"] == "verify_rerun"]
    assert len(verify) == 1 and verify[0]["verify_rerun"] == "failed"
    assert verify[0]["note"].startswith("exit_code=") and not verify[0]["note"].startswith(
        "exit_code=0")


def test_verify_rerun_passes_when_model_actually_fixes_repo(tmp_path):
    """模型真把仓库修绿：模型命令与全量复核都为 0，才算 tests_passed。"""
    repo, script = _setup(tmp_path)
    trace = tmp_path / "trace.jsonl"

    res = run_task(repo, MockModel(script), f"{sys.executable} -m pytest -q",
                   max_steps=5, trace_path=trace)

    assert (res["ok"], res["reason"]) == (True, "tests_passed")
    records = [json.loads(x) for x in trace.read_text(encoding="utf-8").splitlines()]
    verify = [r for r in records if r["tool"] == "verify_rerun"]
    assert len(verify) == 1 and verify[0]["verify_rerun"] == "passed"


def test_shell_meta_cmd_rejected_and_marked_in_trace(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "test_bad.py").write_text(
        "def test_bad():\n    assert False\n", encoding="utf-8")
    script = tmp_path / "script.json"
    script.write_text(json.dumps([
        {"name": "run_tests",
         "args": {"cmd": f"{sys.executable} -m pytest -q | tail -60"}}]), encoding="utf-8")
    trace = tmp_path / "trace.jsonl"

    res = run_task(repo, MockModel(script), f"{sys.executable} -m pytest -q",
                   max_steps=2, trace_path=trace)

    assert res["ok"] is False
    records = [json.loads(x) for x in trace.read_text(encoding="utf-8").splitlines()]
    first = [r for r in records if r["step"] == 1][0]
    assert first["breaker"] == "shell_meta"
    assert "元字符" in first["note"]


def test_max_steps_breaker(tmp_path):
    repo, script = _setup(tmp_path)
    trace = tmp_path / "trace.jsonl"
    res = run_task(repo, MockModel(script), f"{sys.executable} -m pytest -q",
                   max_steps=1, trace_path=trace)
    assert (res["ok"], res["reason"], res["steps"]) == (False, "max_steps", 1)
    assert trace.read_text(encoding="utf-8").count("\n") >= 1
    assert (repo / "calc.py").read_text(encoding="utf-8") == "def add(a, b):\n    return a - b\n"
