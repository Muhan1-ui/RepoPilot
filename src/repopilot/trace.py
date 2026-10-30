"""JSONL 轨迹：一步一行，可回放、可算成本。"""

import json
import time
from pathlib import Path


class TraceWriter:
    """把每次工具调用追加成一行 JSON；args 只留摘要，不落整份文件内容。"""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, step: int, tool: str, args_digest: str, ok: bool,
              duration_ms: float, note: str = "", prompt_tokens: int = 0,
              completion_tokens: int = 0, breaker: str | None = None,
              escalate: str | None = None) -> None:
        """追加一行 trace；tokens 记在该步第一行（模型一轮的消耗）。"""
        rec = {"ts": round(time.time(), 3), "step": step, "tool": tool,
               "args_digest": str(args_digest)[:200], "ok": ok,
               "duration_ms": round(duration_ms, 1), "note": note[:200],
               "prompt_tokens": int(prompt_tokens or 0),
               "completion_tokens": int(completion_tokens or 0)}
        if breaker:
            rec["breaker"] = breaker
        if escalate:
            rec["escalate"] = escalate
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
