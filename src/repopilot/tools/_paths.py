"""路径归一化：仓库内绝对路径按相对路径处理，只有真正越界才报错。"""

from pathlib import Path

# 工具层会在前面拼 "ERROR: "，这里留出余量，保证最终提示不超过 200 字符。
_DIR_HINT_MAX = 190


def _dir_hint(display: str, root: Path) -> str:
    """目录不是"越界"：提示给出具体文件，并列出仓库根下前 20 个条目。"""
    prefix = (f"{display} 是目录，请给出具体文件路径，例如 foo/bar.py；"
              f"仓库内可见的顶层条目前 20 个：")
    try:
        names = sorted(p.name + ("/" if p.is_dir() else "") for p in root.iterdir())
    except OSError:
        names = []
    shown, used = [], len(prefix)
    for name in names[:20]:
        piece = (", " if shown else "") + name
        if used + len(piece) > _DIR_HINT_MAX:
            break
        shown.append(name)
        used += len(piece)
    return prefix + (", ".join(shown) if shown else "(空)")


def resolve_in_repo(path: str, repo: str = ".") -> tuple[str, Path]:
    """返回 ``(相对路径, 绝对路径)``；path 可以是仓库内相对或绝对路径。"""
    root = Path(repo).resolve()
    raw = Path(path)
    target = (raw if raw.is_absolute() else root / raw).resolve()
    if target != root and root not in target.parents:
        raise ValueError(f"path escapes repo: 仓库根是 {root}，你给的是 {path}")
    if target.is_dir():
        display = "." if target == root else target.relative_to(root).as_posix()
        raise ValueError(_dir_hint(display, root))
    return target.relative_to(root).as_posix(), target
