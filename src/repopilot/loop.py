"""Agent loop：模型 → 工具 → 观察，直到测试通过或步数熔断。"""

import json
import re
import time
from pathlib import Path

from .tools import TOOLS, dispatch
from .trace import TraceWriter

MAX_STEPS_DEFAULT = 8
SYSTEM_PROMPT = (
    "你是一个修复 Python 仓库失败单测的 agent。\n"
    "先用 read_file 看代码，再用 apply_patch 提交 unified diff 修复，最后用 run_tests 验证。\n"
    "工具返回 ERROR 时阅读错误并调整，不要重复同样的失败操作。"
)
_EXIT = re.compile(r"exit_code=(-?\d+)")
_HUNK_FAILED = re.compile(r"hunk\b.*\bfailed", re.IGNORECASE)

_FORMAT_SAMPLE = (
    "--- a/f.py\n"
    "+++ b/f.py\n"
    "@@ -1,3 +1,4 @@\n"
    " 上下文行（前导一个空格）\n"
    "-被删除的旧行\n"
    "+新增的行\n"
    " 下一行上下文（同样前导空格）\n"
)


def classify_error(result: str) -> str | None:
    """只看工具返回字符串归类：format / path / other；非 ERROR 返回 None。"""
    if not result.startswith("ERROR"):
        return None
    low = result.lower()
    if ("context mismatch" in low or "patch applies to nothing" in low
            or "malformed hunk" in low or _HUNK_FAILED.search(low)):
        return "format"
    if any(hint in low for hint in ("not found", "escape", "outside repo")):
        return "path"
    return "other"


def _reminder(kind: str) -> str:
    """连续 2 次同类失败后注入的具体提醒（不改变正常路径）。"""
    head = f"提醒：工具已连续 2 次返回同类错误（{kind}）。"
    if kind == "format":
        return (head + "unified diff 必须严格符合下面的格式，"
                "每个上下文行前导一个空格：\n" + _FORMAT_SAMPLE +
                "生成 diff 前必须先调用 read_file，确认当前文件的行号和内容，再生成 diff。")
    if kind == "path":
        return (head + "path 必须是仓库内路径（相对路径或仓库内绝对路径均可）；"
                "先用 read_file 确认文件存在并查看内容，再重试。")
    return head + "先调用 read_file 确认当前文件和内容，不要重复同样的失败调用。"


ESCALATE_REMINDER = (
    "提醒：apply_patch 已连续 3 次失败。放弃 patch，改用最小改动："
    "先用 read_file 读出完整文件，再调用 write_file 一次性给出整文件的新内容"
    "（不要传 diff）。"
)


def _assistant(msg) -> dict:
    """把 SDK / Mock 的 message 统一成可回灌的 assistant dict。"""
    calls = getattr(msg, "tool_calls", None) or []
    return {"role": "assistant", "content": getattr(msg, "content", None),
            "tool_calls": [{"id": c.id, "type": "function",
                            "function": {"name": c.function.name,
                                         "arguments": c.function.arguments}} for c in calls]}


def _exit_code(result: str) -> int | None:
    m = _EXIT.search(result)
    return int(m.group(1)) if m else None


def _record(trace: TraceWriter | None, step: int, tool: str, args: dict,
            result: str, duration_ms: float, prompt_tokens: int = 0,
            completion_tokens: int = 0, breaker: str | None = None,
            escalate: str | None = None) -> None:
    """写一行 trace；args 只留前 200 字符摘要，tokens 记在本步第一行。"""
    if trace:
        note = result.splitlines()[0][:120] if result else ""
        trace.write(step, tool, json.dumps(args, ensure_ascii=False),
                    not result.startswith("ERROR"), duration_ms, note,
                    prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                    breaker=breaker, escalate=escalate)


def run_task(repo, model, test_cmd: str, max_steps: int = MAX_STEPS_DEFAULT,
             trace_path=None, description: str = "", docker: bool = False) -> dict:
    """跑一题，返回 ``{ok, steps, reason, trace_path}``；工具失败只回灌 ERROR，不中断。"""
    repo = str(Path(repo).resolve())
    trace = TraceWriter(trace_path) if trace_path else None
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"任务：{description or '让仓库里的测试全部通过。'}\n"
                                    f"测试命令：{test_cmd}\n仓库根目录：{repo}"},
    ]
    ok, reason, steps = False, "max_steps", 0
    streak_kind, streak_n, reminded = None, 0, 0
    try:
        for step in range(1, max_steps + 1):
            steps = step
            step_meta = {}
            # 同类错误连续 2 次：下一次模型调用前提醒；连续 3 次：升级为整文件策略。
            if streak_n >= 3 and reminded < 3:
                messages.append({"role": "user", "content": ESCALATE_REMINDER})
                step_meta["escalate"] = "whole_file"
                reminded = 3
            elif streak_n == 2 and reminded < 2:
                messages.append({"role": "user", "content": _reminder(streak_kind)})
                step_meta["breaker"] = f"{streak_kind}_repeat"
                reminded = 2
            msg = model.chat(messages, TOOLS)
            usage = getattr(model, "last_usage", None) or {}
            prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
            completion_tokens = int(usage.get("completion_tokens", 0) or 0)
            calls = getattr(msg, "tool_calls", None) or []
            messages.append(_assistant(msg))
            if not calls:
                t0 = time.perf_counter()
                result = dispatch("run_tests", {"cmd": test_cmd}, repo=repo, docker=docker)
                _record(trace, step, "run_tests", {"cmd": test_cmd}, result,
                        (time.perf_counter() - t0) * 1000,
                        prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                        breaker=step_meta.get("breaker"),
                        escalate=step_meta.get("escalate"))
                ok = _exit_code(result) == 0
                reason = "tests_passed" if ok else "no_tool_calls_failed"
                break
            passed = False
            for i, call in enumerate(calls):
                name, args, t0 = call.function.name, {}, time.perf_counter()
                try:
                    args = json.loads(call.function.arguments or "{}")
                    if name == "run_tests":
                        args.setdefault("cmd", test_cmd)
                    result = dispatch(name, args, repo=repo, docker=docker)
                except Exception as e:
                    result = f"ERROR: {e}"
                _record(trace, step, name, args, result, (time.perf_counter() - t0) * 1000,
                        prompt_tokens=prompt_tokens if i == 0 else 0,
                        completion_tokens=completion_tokens if i == 0 else 0,
                        breaker=step_meta.get("breaker") if i == 0 else None,
                        escalate=step_meta.get("escalate") if i == 0 else None)
                messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
                kind = classify_error(result)
                if kind is None:  # 任意一次成功工具调用都清零
                    streak_kind, streak_n, reminded = None, 0, 0
                elif kind == streak_kind:
                    streak_n += 1
                else:
                    streak_kind, streak_n, reminded = kind, 1, 0
                if name == "run_tests" and _exit_code(result) == 0:
                    ok, reason, passed = True, "tests_passed", True
                    break
            if passed:
                break
    except Exception as e:
        reason = f"error: {e}"
    return {"ok": ok, "steps": steps, "reason": reason,
            "trace_path": str(trace_path) if trace_path else None}
