"""评测辅助：一次跑多个 ``repo_clean`` 时，把每个仓库根目录加入 sys.path。

这样 ``pytest eval/bugsets/bug_00*/repo_clean -q`` 能像在各自仓库里一样导入
被测模块；普通 ``pytest tests/`` 不受影响。
"""

import sys
from pathlib import Path


def pytest_configure(config):
    for arg in config.args:
        p = Path(arg)
        if p.name == "repo_clean" and p.is_dir():
            root = str(p.resolve())
            if root not in sys.path:
                sys.path.insert(0, root)
