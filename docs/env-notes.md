# 环境验证记录（2026-10-30）

- Python：3.14.9（`.venv\Scripts\python.exe`），满足 `pyproject.toml` 的 `requires-python = ">=3.12"`。
- pytest：9.2.0；openai：3.41.0；pydantic：2.14.2；httpx：未安装（openai 3.x 改用 httpx2 2.16.0，不再是 httpx 依赖）。
- 冒烟测试：`python -m pytest tests/test_smoke.py -q` → 3 passed，0 failed，耗时 0.02s。
- 依赖安装：一条命令首次即成功，未使用清华镜像重试；python-dotenv 1.2.4、pytest 均为已满足状态，新装 openai 及其传递依赖。
- 为什么用 3.14 不用 3.12：`.venv` 已按本机 3.14.9 建好，且高于 3.12 的最低要求，openai/pydantic/jiter 均有现成 cp314 wheel，无需降级或源码编译。
