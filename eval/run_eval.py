"""批量评测：逐题重置 repo → 真模型跑 run_task → 汇总 pass@1 / 轮数 / token / 成本。

用法：
    python eval/run_eval.py --model real --max-steps 8 --no-docker
    python eval/run_eval.py --model real --max-steps 8 --only bug_0003
"""

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from repopilot.llm import MockModel, OpenAIModel, load_env  # noqa: E402
from repopilot.loop import run_task  # noqa: E402
from repopilot.sandbox import docker_available  # noqa: E402
from repopilot.task import reset_repo  # noqa: E402

DEFAULT_BUGSET = ROOT / "eval" / "bugsets"
REPORTS = ROOT / "eval" / "reports"


def discover(bugset: Path) -> list[Path]:
    """一题一个目录，含 meta.json 即视为有效题；目录名即 task_id。"""
    return sorted(p for p in bugset.iterdir() if (p / "meta.json").exists())


def _tests_untouched(case: Path) -> bool:
    """测试文件与 pytest.ini 必须与初始快照逐字节一致，防止改测试“通过”。"""
    for rel in ("tests", "pytest.ini"):
        clean, repo = case / "repo_clean" / rel, case / "repo" / rel
        if clean.is_dir():
            if not repo.is_dir():
                return False
            src = {p.relative_to(clean) for p in clean.rglob("*") if p.is_file()}
            dst = {p.relative_to(repo) for p in repo.rglob("*") if p.is_file()}
            if src != dst:
                return False
            if any((clean / r).read_bytes() != (repo / r).read_bytes() for r in src):
                return False
        elif clean.is_file():
            if not repo.is_file() or clean.read_bytes() != repo.read_bytes():
                return False
    return True


def _trace_errors(trace_path: Path) -> int:
    """统计 trace 里工具返回 ERROR 的步数（ok=False 或 note 以 ERROR 开头）。"""
    if not trace_path.is_file():
        return 0
    n = 0
    for line in trace_path.read_text(encoding="utf-8").splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not rec.get("ok") or str(rec.get("note", "")).startswith("ERROR"):
            n += 1
    return n


def _fmt_cost(cost: float | None) -> str:
    return "n/a" if cost is None else f"¥{cost:.4f}"


def _print_table(rows: list[dict]) -> None:
    print(f"{'task':<10} {'ok':<4} {'steps':<5} {'prompt':>8} {'compl':>8} "
          f"{'cost':>8} {'sec':>7}  reason")
    for r in rows:
        print(f"{r['task']:<10} {str(r['ok']):<4} {r['steps']:<5} "
              f"{r['prompt_tokens']:>8} {r['completion_tokens']:>8} "
              f"{_fmt_cost(r['cost']):>8} {r['duration_s']:>7.2f}  {r['reason']}")


def _summary(rows: list[dict], max_steps: int) -> dict:
    passed = [r for r in rows if r["ok"]]
    steps_all = [r["steps"] for r in rows]
    steps_ok = [r["steps"] for r in passed]
    total_prompt = sum(r["prompt_tokens"] for r in rows)
    total_completion = sum(r["completion_tokens"] for r in rows)
    costs = [r["cost"] for r in rows]
    total_cost = None if any(c is None for c in costs) else sum(costs)
    return {
        "passed": len(passed),
        "total": len(rows),
        "pass_rate": round(len(passed) / len(rows), 4) if rows else 0.0,
        "avg_steps_passed": round(statistics.mean(steps_ok), 2) if steps_ok else None,
        "avg_steps_all": round(statistics.mean(steps_all), 2) if steps_all else None,
        "total_prompt_tokens": total_prompt,
        "total_completion_tokens": total_completion,
        "total_tokens": total_prompt + total_completion,
        "avg_tokens_per_task": round((total_prompt + total_completion) / len(rows), 1) if rows else 0,
        "total_cost": total_cost,
        "avg_cost_per_task": (round(total_cost / len(rows), 4)
                              if total_cost is not None and rows else None),
        "max_steps_tasks": [r["task"] for r in rows if r["reason"] == "max_steps"],
        "no_tool_calls_failed_tasks": [r["task"] for r in rows
                                       if r["reason"] == "no_tool_calls_failed"],
        "error_tasks": [r["task"] for r in rows if r["error_steps"] > 0
                        or str(r["reason"]).startswith("error:")],
        "tests_modified_tasks": [r["task"] for r in rows if not r["tests_untouched"]],
    }


def _write_markdown(report: dict, path: Path) -> None:
    s, rows = report["summary"], report["tasks"]
    env = report["environment"]
    lines = [
        "# W2 评测报告",
        "",
        f"- 运行时间：{report['started_at']}（run_id `{report['run_id']}`）",
        f"- 模型：`{env['model']}`（mode={report['model_mode']}）",
        f"- 沙箱：{'docker（--network=none）' if report['docker'] else '本机 subprocess（--no-docker）'}",
        f"- max_steps：{report['max_steps']}",
        f"- 单价：输入 {_price_text(env['price_in_per_1m'])} / 输出 "
        f"{_price_text(env['price_out_per_1m'])}（元/百万 token）",
        "",
        "## 三个数字",
        "",
        f"- 通过数：**{s['passed']}/{s['total']}**（{s['pass_rate'] * 100:.1f}%）",
        f"- 平均轮数：**{_num(s['avg_steps_passed'])}**（通过题） / "
        f"{_num(s['avg_steps_all'])}（全部题）",
        f"- 单题成本：**{_fmt_cost(s['avg_cost_per_task'])}**"
        f"（总成本 {_fmt_cost(s['total_cost'])}）",
        "",
        f"- 总 token：{s['total_tokens']}（prompt {s['total_prompt_tokens']} / "
        f"completion {s['total_completion_tokens']}），单题平均 {s['avg_tokens_per_task']}",
        "",
        "## 逐题明细",
        "",
        "| task | ok | steps | prompt | completion | cost | duration(s) | reason | ERROR 步数 | tests 未改 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r['task']} | {r['ok']} | {r['steps']} | {r['prompt_tokens']} | "
                     f"{r['completion_tokens']} | {_fmt_cost(r['cost'])} | "
                     f"{r['duration_s']:.2f} | {r['reason']} | {r['error_steps']} | "
                     f"{r['tests_untouched']} |")
    lines += [
        "",
        "## 失败归因索引",
        "",
        f"- max_steps：{_list(s['max_steps_tasks'])}",
        f"- no_tool_calls_failed：{_list(s['no_tool_calls_failed_tasks'])}",
        f"- 有 ERROR 的题：{_list(s['error_tasks'])}",
        f"- 改过测试的题（判为不通过）：{_list(s['tests_modified_tasks'])}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _num(x) -> str:
    return "n/a" if x is None else f"{x}"


def _list(xs: list[str]) -> str:
    return "、".join(xs) if xs else "无"


def _price_text(x) -> str:
    return "未配置（cost=n/a）" if x is None else f"{x}"


def main() -> int:
    ap = argparse.ArgumentParser(description="跑 10 题 bug 集并产出 W2 三个数字")
    ap.add_argument("--bugset", default=str(DEFAULT_BUGSET))
    ap.add_argument("--model", choices=["real", "mock"], default="real")
    ap.add_argument("--max-steps", type=int, default=8)
    ap.add_argument("--docker", action="store_true",
                    help="在 docker --network=none 容器内跑测试（显式写法，与默认行为一致）")
    ap.add_argument("--no-docker", action="store_true",
                    help="本机 subprocess 跑测试（本机无 docker daemon 时必须显式指定）")
    ap.add_argument("--only", action="append", default=None,
                    help="只跑指定 task_id，可重复；如 --only bug_0003")
    ap.add_argument("--report-name", default="w2-summary",
                    help="报告文件名前缀，写到 eval/reports/<name>.json/.md")
    args = ap.parse_args()

    load_env()
    cases = discover(Path(args.bugset))
    if args.only:
        wanted = set(args.only)
        cases = [c for c in cases if c.name in wanted]
    if not cases:
        print("没有匹配的题目")
        return 2

    if args.docker and args.no_docker:
        ap.error("--docker 与 --no-docker 不能同时使用")
    docker = not args.no_docker
    if docker and not docker_available():
        print("WARNING: docker daemon 不可用，自动降级为本机 subprocess（等同于 --no-docker）")
        docker = False

    run_id = time.strftime("%Y%m%d-%H%M%S")
    started_at = time.strftime("%Y-%m-%d %H:%M:%S")
    rows, model_name = [], "mock" if args.model == "mock" else None
    price_in = price_out = None

    for case in cases:
        meta = json.loads((case / "meta.json").read_text(encoding="utf-8"))
        reset_repo(case)
        if args.model == "mock":
            model = MockModel(case / meta.get("mock_script", "mock_script.json"))
        else:
            model = OpenAIModel()
            model_name = model.model
            price_in, price_out = model.price_in, model.price_out
        trace_path = case / "runs" / run_id / "trace.jsonl"
        t0 = time.perf_counter()
        res = run_task(case / "repo", model, meta.get("test_cmd", "python -m pytest -q"),
                       max_steps=args.max_steps, trace_path=trace_path,
                       description=meta.get("description", ""), docker=docker)
        duration = time.perf_counter() - t0
        cost = model.cost() if hasattr(model, "cost") else None
        tests_untouched = _tests_untouched(case)
        ok = bool(res["ok"]) and tests_untouched
        reason = res["reason"] if tests_untouched else "tests_modified"
        row = {
            "task": case.name,
            "category": meta.get("category", ""),
            "ok": ok,
            "steps": res["steps"],
            "reason": reason,
            "prompt_tokens": int(model.usage["prompt_tokens"]),
            "completion_tokens": int(model.usage["completion_tokens"]),
            "cost": cost,
            "duration_s": round(duration, 2),
            "error_steps": _trace_errors(trace_path),
            "tests_untouched": tests_untouched,
            "trace_path": str(trace_path.relative_to(ROOT)),
        }
        rows.append(row)
        print(f"[{len(rows)}/{len(cases)}] {case.name}: ok={row['ok']} steps={row['steps']} "
              f"reason={row['reason']} tokens={row['prompt_tokens']}/"
              f"{row['completion_tokens']} cost={_fmt_cost(cost)}")

    summary = _summary(rows, args.max_steps)
    report = {
        "run_id": run_id,
        "started_at": started_at,
        "model_mode": args.model,
        "model": model_name,
        "docker": docker,
        "max_steps": args.max_steps,
        "environment": {
            "model": model_name,
            "price_in_per_1m": price_in,
            "price_out_per_1m": price_out,
        },
        "summary": summary,
        "tasks": rows,
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    report_base = REPORTS / args.report_name
    report_json, report_md = report_base.with_suffix(".json"), report_base.with_suffix(".md")
    report_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_markdown(report, report_md)

    print()
    _print_table(rows)
    print()
    print(f"通过 {summary['passed']}/{summary['total']} "
          f"({summary['pass_rate'] * 100:.1f}%) | "
          f"平均轮数 {_num(summary['avg_steps_passed'])}/{_num(summary['avg_steps_all'])} | "
          f"总 token {summary['total_tokens']} | 单题成本 {_fmt_cost(summary['avg_cost_per_task'])}")
    print(f"报告：{report_json} / {report_md}")
    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
