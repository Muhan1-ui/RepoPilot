"""LLM 薄封装：OpenAI 兼容接口 + 可复现的 MockModel + token/成本统计。"""

import json
import os
from pathlib import Path
from types import SimpleNamespace

DEFAULT_MODEL = "deepseek-chat"
DEFAULT_ENV_FILE = ".env"


def load_env(path: str | Path | None = None) -> None:
    """用 python-dotenv 在进程内读 .env（不覆盖已有环境变量，不打印任何值）。"""
    path = path or os.getenv("REPOPILOT_ENV_FILE") or DEFAULT_ENV_FILE
    p = Path(path)
    if p.is_file():
        from dotenv import load_dotenv  # 延迟导入：--mock / 单测不依赖 dotenv
        load_dotenv(p, override=False)


def _price(name: str) -> float | None:
    """读每百万 token 单价（元）；缺失或非法返回 None，绝不猜价格。"""
    raw = os.getenv(name)
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _usage_of(resp) -> dict:
    """从 SDK 响应里取 usage；没有就记 0。"""
    u = getattr(resp, "usage", None)
    return {"prompt_tokens": int(getattr(u, "prompt_tokens", 0) or 0),
            "completion_tokens": int(getattr(u, "completion_tokens", 0) or 0)}


class OpenAIModel:
    """OpenAI 兼容客户端；换厂商只改 LLM_BASE_URL，不 import httpx。"""

    def __init__(self, model: str | None = None) -> None:
        load_env()
        from openai import OpenAI  # 延迟导入：--mock 与单测不需要网络

        self.model = model or os.getenv("LLM_MODEL", DEFAULT_MODEL)
        self.client = OpenAI(base_url=os.getenv("LLM_BASE_URL") or None,
                             api_key=os.getenv("LLM_API_KEY") or "missing")
        self.usage = {"prompt_tokens": 0, "completion_tokens": 0}
        self.last_usage = {"prompt_tokens": 0, "completion_tokens": 0}
        self.price_in = _price("LLM_PRICE_IN_PER_1M")
        self.price_out = _price("LLM_PRICE_OUT_PER_1M")

    def chat(self, messages: list[dict], tools: list[dict] | None = None):
        """调一轮 chat.completions；累积 usage 并返回 message。"""
        resp = self.client.chat.completions.create(
            model=self.model, messages=messages, tools=tools or None)
        self.last_usage = _usage_of(resp)
        for k, v in self.last_usage.items():
            self.usage[k] += v
        return resp.choices[0].message

    def cost(self) -> float | None:
        """按 .env 的单价算累计成本（元）；任一单价缺失返回 None。"""
        if self.price_in is None or self.price_out is None:
            return None
        return (self.usage["prompt_tokens"] / 1e6 * self.price_in
                + self.usage["completion_tokens"] / 1e6 * self.price_out)


class MockModel:
    """按 JSON 脚本依次吐出预设 tool_call；脚本用完返回 content="done"。"""

    def __init__(self, script_path: str | Path) -> None:
        self._script = json.loads(Path(script_path).read_text(encoding="utf-8"))
        self._i = 0
        self.usage = {"prompt_tokens": 0, "completion_tokens": 0}
        self.last_usage = {"prompt_tokens": 0, "completion_tokens": 0}

    def chat(self, messages: list[dict], tools: list[dict] | None = None):
        """返回下一个 tool_call，arguments 是 JSON 字符串，形状与真实 SDK 一致。"""
        self.last_usage = {"prompt_tokens": 0, "completion_tokens": 0}
        if self._i >= len(self._script):
            return SimpleNamespace(content="done", tool_calls=None)
        item = self._script[self._i]
        self._i += 1
        fn = SimpleNamespace(name=item["name"],
                             arguments=json.dumps(item.get("args", {}), ensure_ascii=False))
        call = SimpleNamespace(id=f"call_{self._i}", type="function", function=fn)
        return SimpleNamespace(content=None, tool_calls=[call])

    def cost(self) -> float | None:
        return None
