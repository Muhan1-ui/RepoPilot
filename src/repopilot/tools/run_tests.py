"""run_tests：子进程（或 docker 容器）跑 pytest，带超时与输出截断。"""

import os
import subprocess
import sys
from pathlib import Path

from ..feedback import format_pytest_failure
from ..sandbox import run_in_docker

TIMEOUT, TAIL_LINES = 60, 40


def _tail(text: str) -> str:
    lines = text.splitlines()
    if len(lines) <= TAIL_LINES:
        return "\n".join(lines)
    return f"…(前 {len(lines) - TAIL_LINES} 行已截断)\n" + "\n".join(lines[-TAIL_LINES:])


def run_tests(cmd: str | None = None, *, repo: str = ".", timeout: int = TIMEOUT,
              docker: bool = False) -> str:
    """在 repo 根目录执行测试命令。

    成功：``exit_code=0`` + 输出尾部；失败：``exit_code=N`` + 结构化失败摘要。
    沙箱模式把整条命令包进 ``docker run --network=none``，镜像需自带 pytest。
    """
    cmd = cmd or "python -m pytest -q"
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
