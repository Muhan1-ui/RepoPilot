"""read_file：读取仓库内文件的行区间。"""

from ._paths import resolve_in_repo

MAX_LINES = 200


def read_file(path: str, start: int = 1, end: int | None = None, *, repo: str = ".") -> str:
    """读取 repo 内 path 的第 start~end 行，返回 ``行号|内容``；越界路径返回 ERROR。"""
    try:
        _, target = resolve_in_repo(path, repo)
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        start = max(1, start)
        if start > len(lines):
            return f"ERROR: start={start} beyond EOF ({len(lines)} lines)"
        wanted = min(end or len(lines), len(lines))
        last = min(wanted, start - 1 + MAX_LINES)
        body = "\n".join(f"{i}|{lines[i - 1]}" for i in range(start, last + 1))
        return body + (f"\n…(truncated, 共 {len(lines)} 行)" if last < wanted else "")
    except Exception as e:
        return f"ERROR: {e}"
