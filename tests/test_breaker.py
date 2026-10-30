"""Repeat breaker 自测：同类失败连续 2 次提醒、3 次升级、成功一次后清零。"""

import json
import sys

from repopilot.llm import MockModel
from repopilot.loop import run_task

# 行号故意越界，apply_patch 会返回 "hunk 1 failed: context mismatch"。
BAD_PATCH = ("--- a/calc.py\n+++ b/calc.py\n@@ -9,3 +9,3 @@\n"
             " def add(a, b):\n-    return a - b\n+    return a + b\n")


class RecordingModel(MockModel):
    """在 MockModel 之上记录每次 chat 看到的 messages，供断言提醒内容。"""

    def __init__(self, script_path):
        super().__init__(script_path)
        self.calls = []

    def chat(self, messages, tools=None):
        self.calls.append([dict(m) for m in messages])
        return super().chat(messages, tools)


def _setup(tmp_path, steps):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    (repo / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n", encoding="utf-8")
    script = tmp_path / "script.json"
    script.write_text(json.dumps(steps), encoding="utf-8")
    return repo, script


def _patch_step():
    return {"name": "apply_patch", "args": {"patch": BAD_PATCH}}


def _records(trace):
    return [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]


def test_format_reminder_then_escalate(tmp_path):
    repo, script = _setup(tmp_path, [_patch_step()] * 3)
    model = RecordingModel(script)
    trace = tmp_path / "trace.jsonl"
    res = run_task(repo, model, f"{sys.executable} -m pytest -q",
                   max_steps=4, trace_path=trace)

    third = "\n".join(str(m.get("content") or "") for m in model.calls[2])
    assert "@@ -1,3 +1,4 @@" in third
    assert "先调用 read_file" in third and "上下文行" in third

    fourth = "\n".join(str(m.get("content") or "") for m in model.calls[3])
    assert "放弃 patch" in fourth and "write_file" in fourth

    by_step = {r["step"]: r for r in _records(trace)}
    assert by_step[3]["breaker"] == "format_repeat"
    assert "breaker" not in by_step[1] and "breaker" not in by_step[2]
    assert res["ok"] is False


def test_success_resets_streak(tmp_path):
    repo, script = _setup(tmp_path, [
        _patch_step(), _patch_step(),
        {"name": "read_file", "args": {"path": "calc.py"}},  # 成功一次 → 清零
        _patch_step(), _patch_step(), _patch_step(),
    ])
    trace = tmp_path / "trace.jsonl"
    run_task(repo, RecordingModel(script), f"{sys.executable} -m pytest -q",
             max_steps=8, trace_path=trace)

    by_step = {r["step"]: r for r in _records(trace)}
    assert by_step[3]["breaker"] == "format_repeat"          # 第一轮累积
    assert "breaker" not in by_step[4] and "breaker" not in by_step[5]  # 已清零
    assert by_step[6]["breaker"] == "format_repeat"          # 重新累积到 2 次
    assert by_step[7]["escalate"] == "whole_file"            # 重新累积到 3 次
