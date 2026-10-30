# RepoPilot

给一个 Python 仓库加一个失败的单元测试，agent 自己定位文件、改代码、跑测试、看失败输出再改，最后交出 diff 和轨迹。

```bash
pip install -e ".[dev]" && cp .env.example .env   # 填 LLM_API_KEY / LLM_BASE_URL / LLM_MODEL
python -m repopilot run --task eval/bugsets/bug_0001 --mock --max-steps 8   # 无 key 也能跑
python -m repopilot run --task eval/bugsets/bug_0001 --max-steps 8          # 真实模型

# 10 题评测（本机无 docker daemon 时必须 --no-docker）
python eval/run_eval.py --model real --max-steps 8 --no-docker
```

**当前状态：W2**——Agent Loop + 3 个工具（read_file / apply_patch / run_tests）+ 10 道
自建 bug 题（5 类注入 bug）+ 结构化失败回灌（用例名 / 断言差异 / file:line，≤800 字符）
+ 每步 token 统计 + 单题成本（`.env` 未配单价时输出 `n/a`，不猜价格）+ JSONL 轨迹。

- 评测报告：`eval/reports/w2-summary.md`（含通过数、平均轮数、token、成本）
- 环境与 docker 结论：`docs/w2-notes.md`
- 失败归因：`docs/failure-analysis.md`
- docker 沙箱分支已实现（`--docker`）；本机 daemon 不可用，真实评测均走 `--no-docker`，
  安全隔离未在容器内验证。镜像需预装 pytest，可用 `REPOPILOT_DOCKER_IMAGE` 指定。
