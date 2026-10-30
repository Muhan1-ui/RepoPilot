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
    assert [x["tool"] for x in lines] == ["read_file", "apply_patch", "run_tests"]
    assert all(len(x["args_digest"]) <= 200 for x in lines)


def test_max_steps_breaker(tmp_path):
    repo, script = _setup(tmp_path)
    trace = tmp_path / "trace.jsonl"
    res = run_task(repo, MockModel(script), f"{sys.executable} -m pytest -q",
                   max_steps=1, trace_path=trace)
    assert (res["ok"], res["reason"], res["steps"]) == (False, "max_steps", 1)
    assert trace.read_text(encoding="utf-8").count("\n") >= 1
    assert (repo / "calc.py").read_text(encoding="utf-8") == "def add(a, b):\n    return a - b\n"
