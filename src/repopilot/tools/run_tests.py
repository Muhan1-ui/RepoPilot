"""run_tests：子进程（或 docker 容器）跑 pytest，带超时与输出截断。"""

import os
import subprocess
import sys
from pathlib import Path

from ..feedback import format_pytest_failure
from ..sandbox import run_in_docker

TIMEOUT, TAIL_LINES = 60, 40
DEFAULT_CMD = "python -m pytest -q"

# 会吞掉 pytest 退出码的 shell 构造（管道取末环、分号取末条、重定向等）。
SHELL_META = ("|", ";", "&&", "||", "$(", "`", ">", ">>")
SHELL_META_ERROR = (
    "ERROR: 不允许在 cmd 里使用 shell 元字符（| ; && > 等），退出码会被吞掉。"
    "只传 pytest 参数，例如 \"-q tests/\"；完整命令由 harness 拼接。"
)


def has_shell_meta(cmd: str) -> bool:
    """cmd 里是否含会让 ``p.returncode`` 不再代表 pytest 的 shell 构造。"""
    return any(meta in cmd for meta in SHELL_META)


def _tail(text: str) -> str:
    lines = text.splitlines()
    if len(lines) <= TAIL_LINES:
        return "\n".join(lines)
    return f"…(前 {len(lines) - TAIL_LINES} 行已截断)\n" + "\n".join(lines[-TAIL_LINES:])


def run_tests(cmd: str | None = None, *, repo: str = ".", timeout: int = TIMEOUT,
              docker: bool = False, trusted: bool = False) -> str:
    """在 repo 根目录执行测试命令。

    成功：``exit_code=0`` + 输出尾部；失败：``exit_code=N`` + 结构化失败摘要。
    沙箱模式把整条命令包进 ``docker run --network=none``，镜像需自带 pytest。

    模型给的 cmd 先过 shell 元字符检查：``pytest ... | tail`` 这类写法退出码取
    管道末环，会把失败伪装成 0。``trusted=True`` 仅供 harness 用题目原始
    ``test_cmd`` 复核时使用（不经过滤）。
    """
    cmd = cmd or DEFAULT_CMD
    if not trusted and has_shell_meta(cmd):
        return SHELL_META_ERROR
    try:
        if docker:
            # 命令原样交给镜像自带的 python，不换成宿主机的 .venv。
            p = run_in_docker(repo, cmd, timeout=timeout)
        else:
            env = dict(os.environ)
            env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
            p = subprocess.run(cmd, cwd=repo, shell=True, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=timeout, env=env)
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or "") + (e.stderr or "")
        if isinstance(out, bytes):
            out = out.decode("utf-8", "replace")
        return f"ERROR: timeout after {timeout}s\n{_tail(out)}"
    except Exception as e:
        return f"ERROR: {e}"
    if p.returncode == 0:
        return f"exit_code=0\n{_tail(p.stdout + p.stderr)}"
    return f"exit_code={p.returncode}\n{format_pytest_failure(p.stdout, p.stderr)}"
