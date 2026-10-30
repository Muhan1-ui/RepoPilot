"""apply_patch：用标准库应用 unified diff，失败整批回滚。"""

import re
import shutil
import tempfile
from pathlib import Path

from ._paths import resolve_in_repo

_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


class PatchError(RuntimeError):
    """diff 无法干净应用。"""


def _clean(raw: str) -> str | None:
    p = raw.split("\t")[0].strip()
    return None if p == "/dev/null" else (p[2:] if p[:2] in ("a/", "b/") else p)


def _parse(patch: str) -> list[tuple[str, list[tuple[int, list[str]]]]]:
    """解析成 [(path, [(old_start, hunk_lines), ...])]，按行数消费 hunk。"""
    lines, files, i = patch.splitlines(keepends=True), [], 0
    while i < len(lines):
        if not lines[i].startswith("--- "):
            i += 1
            continue
        old = _clean(lines[i][4:])
        if i + 1 >= len(lines) or not lines[i + 1].startswith("+++ "):
            raise PatchError("missing +++ header")
        path, i, hunks = _clean(lines[i + 1][4:]) or old, i + 2, []
        while i < len(lines) and lines[i].startswith("@@"):
            m = _HUNK.match(lines[i])
            if not m:
                raise PatchError(f"bad hunk header: {lines[i].strip()}")
            left = [int(m.group(2) or 1), int(m.group(4) or 1)]
            body, i = [], i + 1
            while i < len(lines) and (left[0] or left[1]):
                tag = lines[i][:1]
                if tag == "\\":
                    i += 1
                    continue
                if tag not in " -+":
                    raise PatchError("malformed hunk body")
                if tag in " -":
                    left[0] -= 1
                if tag in " +":
                    left[1] -= 1
                body.append(lines[i])
                i += 1
            hunks.append((int(m.group(1)), body))
        if not hunks:
            raise PatchError(f"no hunks for {path}")
        files.append((path, hunks))
    if not files:
        raise PatchError("no file sections found")
    return files


def _apply(orig: list[str], hunks: list[tuple[int, list[str]]],
           path: str) -> tuple[list[str], list[int]]:
    """逐 hunk 在声明的行号处核对上下文，返回新内容和新增/修改行号。"""
    out, pos, changed = [], 0, []
    for no, (start, body) in enumerate(hunks, 1):
        old = [line[1:] for line in body if line[0] in " -"]
        idx = max(0, start - 1)
        if old and orig[idx:idx + len(old)] != old:
            raise PatchError(f"hunk {no} failed: context mismatch in {path} near line {start}")
        out.extend(orig[pos:idx])
        for line in body:
            if line[0] == "+":
                changed.append(len(out) + 1)
                out.append(line[1:])
            elif line[0] == " ":
                out.append(line[1:])
        pos = idx + len(old)
    return out + orig[pos:], changed


def apply_patch(patch: str, *, repo: str = ".") -> str:
    """应用 unified diff；任一 hunk 失败则还原所有受影响文件。"""
    root = Path(repo).resolve()
    try:
        files = _parse(patch)
        targets = {}
        for rel, _ in files:
            norm, target = resolve_in_repo(rel, repo)
            if not target.is_file():
                raise PatchError(f"bad path or missing file: {rel} (仓库根是 {root})")
            targets[rel] = (norm, target)
        with tempfile.TemporaryDirectory() as tmp:
            backups = {}
            for rel, (norm, target) in targets.items():
                backup = Path(tmp) / norm
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
                backups[rel] = backup
            try:
                done = []
                for rel, hunks in files:
                    norm, target = targets[rel]
                    orig = target.read_text(encoding="utf-8").splitlines(keepends=True)
                    new, changed = _apply(orig, hunks, norm)
                    with open(target, "w", encoding="utf-8", newline="") as f:
                        f.write("".join(new))
                    span = f"{changed[0]}-{changed[-1]}" if changed else "仅删除"
                    done.append(f"{norm}: {len(changed)} 行新增/修改，新行号 {span}")
                return "OK\n" + "\n".join(done)
            except Exception:
                for rel, backup in backups.items():
                    shutil.copy2(backup, targets[rel][1])
                raise
    except Exception as e:
        return f"ERROR: {e}"
