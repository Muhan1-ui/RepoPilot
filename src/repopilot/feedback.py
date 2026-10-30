"""把 pytest 输出压缩成结构化失败摘要，供下一轮回灌给模型。

目标：模型不需要在 40 行尾部里自己找 ``FAILED`` / 断言差异 / 行号，
一次回灌就能看到「哪条用例、哪一行、期望什么、实际什么」。
解析失败时降级为输出尾部，绝不抛异常。
"""

import re

MAX_CHARS = 800
FALLBACK_LINES = 20

_FAILED = re.compile(r"^FAILED\s+(\S+?)(?:\s+-\s+(.*))?$")
_LOC = re.compile(r"^(\S+?\.py):(\d+):")
_SECTION = re.compile(r"^_{3,}\s+(.+?)\s+_{3,}$")
_ASSERT = re.compile(r"^E(?:\s+|$)(.*)$")


def _tail(text: str, n: int = FALLBACK_LINES) -> str:
    lines = [x for x in text.splitlines() if x.strip()]
    return "\n".join(lines[-n:])


def _sections(stdout: str) -> list[dict]:
    """切出 pytest 的每个 FAILURES 小节，收集 E 行与最后的 file:line。"""
    sections: list[dict] = []
    current: dict | None = None
    for raw in stdout.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if stripped.startswith("_") and stripped.endswith("_"):
            m = _SECTION.match(stripped)
            if m:
                current = {"title": m.group(1).strip(), "asserts": [], "loc": ""}
                sections.append(current)
                continue
        if current is None:
            continue
        m = _ASSERT.match(line)
        if m and m.group(1).strip():
            current["asserts"].append(m.group(1).strip())
        loc = _LOC.match(line)
        if loc:
            # 取最后一条：traceback 末尾才是断言真正所在的行。
            current["loc"] = f"{loc.group(1)}:{loc.group(2)}"
    return sections


def _base(name: str) -> str:
    """去掉参数化后缀与 nodeid 前缀，只留用例函数名。"""
    return name.rsplit("::", 1)[-1].split("[", 1)[0]


def _match_section(name: str, sections: list[dict]) -> dict | None:
    base = _base(name)
    for sec in sections:
        if _base(sec["title"]) == base:
            return sec
    return None


def _parse_failures(stdout: str) -> list[dict]:
    """按 FAILED 行抽取失败用例，并把断言差异 / 位置合并进来。"""
    sections = _sections(stdout)
    failures: list[dict] = []
    seen: set[str] = set()
    for raw in stdout.splitlines():
        m = _FAILED.match(raw.strip())
        if not m:
            continue
        name = m.group(1)
        if name in seen:
            continue
        seen.add(name)
        sec = _match_section(name, sections) or {"asserts": [], "loc": ""}
        asserts = sec["asserts"]
        if not asserts and m.group(2):
            asserts = [m.group(2).strip()]
        loc = sec["loc"]
        if not loc and "::" in name:
            loc = name.split("::", 1)[0]
        failures.append({"name": name, "loc": loc, "asserts": asserts})
    return failures


def _render(failures: list[dict], total: int | None = None) -> str:
    """把失败列表渲染成紧凑文本（不加截断说明）；header 用总失败数。"""
    header = f"pytest 失败 {total if total is not None else len(failures)} 条："
    blocks: list[str] = []
    for i, f in enumerate(failures, 1):
        block = [f"{i}) FAILED {f['name']}" + (f" @ {f['loc']}" if f["loc"] else "")]
        block += [f"   {a}" for a in f["asserts"][:4]]
        blocks.append("\n".join(block))
    return header + "\n" + "\n".join(blocks)


def _truncate(text: str, omitted: int) -> str:
    """硬截断到 MAX_CHARS；omitted 为因条数上限没列出的用例数。"""
    suffix = f"\n…另有 {omitted} 条未列出" if omitted else "\n…(输出已截断)"
    if len(text) + len(suffix) <= MAX_CHARS:
        return text + (suffix if omitted else "")
    budget = MAX_CHARS - len(suffix)
    return text[: max(0, budget)].rstrip() + suffix


def format_pytest_failure(stdout: str, stderr: str = "", max_failures: int = 3) -> str:
    """把 pytest 失败输出压成 ≤800 字符的紧凑文本。

    优先输出 ``FAILED 用例名 @ file:line`` + 断言差异（``E`` 行）。
    一条都解析不出来时退化为「输出尾部 20 行」，任何情况下都不抛异常。
    """
    try:
        stdout = stdout or ""
        stderr = stderr or ""
        failures = _parse_failures(stdout)
        if not failures:
            body = _tail(stdout + ("\n" + stderr if stderr else ""))
            if not body.strip():
                return "pytest 失败，但 stdout/stderr 为空（退出码非 0）。"
            text = "pytest 输出无法解析失败用例，尾部 %d 行：\n%s" % (FALLBACK_LINES, body)
            return _truncate(text, 0)
        max_failures = max(1, int(max_failures))
        shown = failures[:max_failures]
        text = _render(shown)
        omitted = len(failures) - len(shown)
        if len(text) > MAX_CHARS:
            # 先逐条丢掉末尾用例，再硬截断，保证 ≤800。
            while len(shown) > 1:
                shown.pop()
                omitted += 1
                text = _render(shown)
                if len(text) <= MAX_CHARS:
                    break
        return _truncate(text, omitted)
    except Exception as e:  # 兜底：结构化失败摘要本身绝不能再炸掉 agent loop
        try:
            tail = _tail((stdout or "") + "\n" + (stderr or ""))
            return _truncate(f"pytest 失败（摘要解析异常: {type(e).__name__}）\n{tail}", 0)
        except Exception:
            return "pytest 失败（无法读取输出）。"
