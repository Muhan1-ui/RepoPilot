# W2 环境与运行记录（2026-10-30）

## Docker

> **历史记录（2026-10-30 原始结论，保留以备追溯）**
>
> - `docker --version` → **可用**：`Docker version 29.3.1, build c2be9cc`。
> - `docker info` → **退出码 1**：CLI 在，但 daemon 连不上（Docker Desktop 未启动）。
> - 没有尝试安装、没有联网下载镜像。
> - 因此：**本机无可用 docker daemon，评测未在容器内执行，安全隔离未验证。**
>   W2 的 docker 分支（`build_docker_cmd` 纯函数 + `run_tests(docker=True)`）已实现并
>   由单测覆盖命令形状；真实评测一律走 `--no-docker` 的本机 subprocess。
> - 接入 docker 时注意：默认镜像 `python:3.12-slim` 不含 pytest，需要用
>   `REPOPILOT_DOCKER_IMAGE` 指向预装 pytest 的镜像（例如自建 `repopilot-py:3.12`）。

### 镜像与隔离验证（2026-10-31 补测，已实测）

上述"daemon 不可用 / 隔离未验证"的说法已被本轮实测取代。Docker Desktop 已启动，
镜像按 `docker/Dockerfile` 构建完成（基础镜像 `python:3.12-slim`，构建期联网装依赖），
镜像内 pytest 版本为 **9.2.0**。

镜像列表：

```text
$ docker images --format "{{.Repository}}:{{.Tag}} {{.Size}}" | grep repopilot
repopilot-sandbox:pytest9 210MB
```

镜像内 pytest 版本：

```text
$ docker run --rm repopilot-sandbox:pytest9 python -m pytest --version
pytest 9.2.0
```

**隔离正例（必须失败，实际 exit=1）**：

```text
$ docker run --rm --network=none repopilot-sandbox:pytest9 python -c "import socket; socket.create_connection(('1.1.1.1', 80), 3)" ; echo "exit=$?"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/usr/local/lib/python3.12/socket.py", line 865, in create_connection
    raise exceptions[0]
  File "/usr/local/lib/python3.12/socket.py", line 850, in create_connection
    sock.connect(sa)
OSError: [Errno 101] Network is unreachable
exit=1
```

**隔离反例（必须成功，实际 exit=0）**：

```text
$ docker run --rm repopilot-sandbox:pytest9 python -c "import urllib.request;print(urllib.request.urlopen('https://pypi.org',timeout=8).status)" ; echo "exit=$?"
200
exit=0
```

**结论**：同一镜像在 `--network=none` 下外连失败（`Errno 101 Network is unreachable`），
去掉该参数后立即连通（HTTP 200）。因此**隔离来自 `--network=none`，不是环境无网**——
宿主机/容器本身是有网的，断网是运行时显式施加的。评测时应始终带 `--network=none`；
上述反例仅用于证明该开关确实生效。

## LLM 配置

- 仓库里**没有 `.env`**，只有 `.env.example`；本次通过 python-dotenv 在进程内读取
  （`REPOPILOT_ENV_FILE=.env.example`），全程未打印/未落盘任何 key。
- 实际使用的模型：**`deepseek-flash`**（`LLM_BASE_URL=https://api.deepseek.com`），
  连通性与 tool-calling 验证和正式评测日期均为 **2026-10-30**。
- `LLM_PRICE_IN_PER_1M` / `LLM_PRICE_OUT_PER_1M` **未配置**，因此报告中的成本一律为
  `n/a`，没有自行填任何价格。
- 安全处理：`.env.example` 原先含一把真实格式的 key；评测结束后已替换为
  `your-key-here` 占位符，并扫描确认 trace / 报告 / 文档 / 测试中没有 key 泄漏。

## 运行环境

- Python 3.14.9（`.venv/Scripts/python.exe`），pytest 9.2.0，openai 3.41.0，
  python-dotenv 1.2.4。
- 本机平台：Windows 11，shell 为 Git Bash。

## 复现命令

```bash
cd D:/repopilot
.venv/Scripts/python.exe -m pytest tests/ -q
.venv/Scripts/python.exe -m repopilot run --task eval/bugsets/bug_0001 --mock --max-steps 8
.venv/Scripts/python.exe -m pytest eval/bugsets/bug_00*/repo_clean -q   # 10 题初始应全红
python eval/run_eval.py --model real --max-steps 8 --no-docker
cat eval/reports/w2-summary.md
```

> 注：任务书里的 `bug_0000*/repo_clean` 通配符匹配不到任何目录（`bug_0001` 的第四位是
> `1`，不是 `0`），实际使用 `bug_00*` 覆盖 bug_0001 ~ bug_0010。仓库根目录的
> `conftest.py` 会把各 `repo_clean` 加入 `sys.path`，让一条 pytest 命令能跑完 10 题。
