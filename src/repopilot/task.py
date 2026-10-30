"""题目目录操作：用 repo_clean 重置 repo，保证每题可复现地重跑。"""

import shutil
from pathlib import Path


def reset_repo(task: str | Path) -> None:
    """把 ``repo_clean`` 整体复制成 ``repo``；没有 repo_clean 时什么都不做。"""
    task = Path(task)
    clean, repo = task / "repo_clean", task / "repo"
    if clean.is_dir():
        if repo.exists():
            shutil.rmtree(repo)
        shutil.copytree(clean, repo)
