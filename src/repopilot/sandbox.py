"""沙箱：把测试命令包成一行 docker run，默认断网、只挂工作区、限资源。"""

import os
import subprocess
from pathlib import Path

IMAGE = "repopilot-sandbox:pytest9"


def _image() -> str:
    """允许用 REPOPILOT_DOCKER_IMAGE 换成预装 pytest 的镜像。"""
    return os.getenv("REPOPILOT_DOCKER_IMAGE") or IMAGE


def build_docker_cmd(repo_path: str, cmd: str, image: str | None = None) -> list[str]:
    """返回可直接交给 subprocess 的 docker run argv。"""
    root = Path(repo_path).resolve().as_posix()
    return ["docker", "run", "--rm", "--network=none", "--memory=1g", "--cpus=1",
            "-v", f"{root}:/ws", "-w", "/ws", image or _image(), "sh", "-lc", cmd]


def run_in_docker(repo: str, cmd: str, image: str | None = None,
                  timeout: int = 60) -> subprocess.CompletedProcess:
    """在 ``--network=none`` 容器里跑命令；命令原样交给镜像自带的 python。"""
    argv = build_docker_cmd(repo, cmd, image=image)
    return subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout)


def docker_available(timeout: int = 5) -> bool:
    """docker CLI 在且 daemon 可连（``docker info`` 退出码 0）。"""
    try:
        p = subprocess.run(["docker", "info"], capture_output=True, timeout=timeout)
        return p.returncode == 0
    except Exception:
        return False
