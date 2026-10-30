"""命令行入口：python -m repopilot run --task <dir> [--mock] ..."""

import argparse
import json
import time
from pathlib import Path

from .llm import MockModel, OpenAIModel
from .loop import run_task
from .task import reset_repo


def _run(args: argparse.Namespace) -> int:
    task = Path(args.task).resolve()
    if not (task / "meta.json").is_file():
        print(f"ERROR: meta.json not found in {task}")
        return 2
    meta = json.loads((task / "meta.json").read_text(encoding="utf-8"))
    if not args.no_reset:
        reset_repo(task)
    test_cmd = args.test_cmd or meta.get("test_cmd", "python -m pytest -q")
    trace_path = task / "runs" / time.strftime("%Y%m%d-%H%M%S") / "trace.jsonl"
    model = (MockModel(task / meta.get("mock_script", "mock_script.json"))
             if args.mock else OpenAIModel())
    result = run_task(task / "repo", model, test_cmd, max_steps=args.max_steps,
                      trace_path=trace_path, description=meta.get("description", ""),
                      docker=args.docker)
    print(f"ok={result['ok']} steps={result['steps']} reason={result['reason']}")
    if isinstance(model, OpenAIModel):
        cost = model.cost()
        print(f"tokens={model.usage['prompt_tokens']}/{model.usage['completion_tokens']} "
              f"cost={'n/a' if cost is None else f'{cost:.4f}'}")
    print(f"trace={result['trace_path']}")
    return 0 if result["ok"] else 1


def main(argv: list[str] | None = None) -> int:
    """解析参数并执行子命令；成功 0，失败 1，输入错误 2。"""
    p = argparse.ArgumentParser(prog="repopilot", description="让 agent 自己修好失败的 Python 单测。")
    sub = p.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="跑单题")
    run.add_argument("--task", required=True, help="题目目录（含 meta.json / repo_clean）")
    run.add_argument("--mock", action="store_true", help="用预设脚本代替真实 LLM")
    run.add_argument("--max-steps", type=int, default=8, help="步数熔断上限")
    run.add_argument("--test-cmd", default=None, help="覆盖 meta.json 里的测试命令")
    run.add_argument("--no-reset", action="store_true", help="不重置 repo，保留上次改动")
    sandbox = run.add_mutually_exclusive_group()
    sandbox.add_argument("--docker", action="store_true",
                         help="在 docker（--network=none）里跑测试；默认本机 subprocess")
    sandbox.add_argument("--no-docker", action="store_false", dest="docker",
                         help="显式使用本机 subprocess（默认行为）")
    return _run(p.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
