FROM python:3.12-slim

# 评测题只依赖 pytest；镜像里预装好，容器内就能直接 `python -m pytest`。
RUN pip install --no-cache-dir "pytest>=9,<10"

WORKDIR /ws

# 不往宿主机挂载目录里写 __pycache__，避免污染被测仓库。
ENV PYTHONDONTWRITEBYTECODE=1
