"""write_file：整文件覆盖写入，供 apply_patch 连续失败后的降级策略使用。"""

from ._paths import resolve_in_repo


def write_file(path: str, content: str, *, repo: str = ".") -> str:
    """把 content 整体写入 repo 内 path；越界路径返回 ERROR。"""
    try:
        rel, target = resolve_in_repo(path, repo)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"OK: wrote {rel} ({len(content.splitlines())} lines)"
    except Exception as e:
        return f"ERROR: {e}"
