# RepoPilot

## 1. 一句话

给一个 Python 仓库加一个失败的单元测试，agent 自己定位文件、改代码、跑测试、看失败输出再改，最后交出 diff 和 JSONL 轨迹。

## 2. 3 分钟跑通（不花钱、不需要 key）

需要 Python ≥ 3.12（实测 3.14.9）。仓库里没有 `requirements.txt`，按下面几行照抄即可。`--mock` 用预设脚本代替真实模型，全程不联网。

Windows PowerShell（PyCharm 默认终端）：

```powershell
git clone <你的仓库地址>; cd repopilot
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e . pytest openai python-dotenv
.venv\Scripts\python.exe -m repopilot run --task eval/bugsets/bug_0001 --mock --max-steps 8
```

Git Bash / macOS / Linux：

```bash
git clone <你的仓库地址> && cd repopilot
python -m venv .venv
.venv/bin/python -m pip install -e . pytest openai python-dotenv      # Windows 用 .venv/Scripts/python.exe
.venv/bin/python -m repopilot run --task eval/bugsets/bug_0001 --mock --max-steps 8
```

`pip install -e .` 会把 `repopilot` 装进当前 venv，之后用 venv 里的 python 在任意目录都能跑 `python -m repopilot --help`。但 `--task` 是相对当前目录解析的：离开仓库目录后要传绝对路径，例如 `.venv\Scripts\python.exe -m repopilot run --task D:/repopilot/eval/bugsets/bug_0001 --mock`。

预期输出（第一行固定，trace 路径带时间戳）：

```text
ok=True steps=3 reason=tests_passed
trace=D:\repopilot\eval\bugsets\bug_0001\runs\<timestamp>\trace.jsonl
```

跑完后可以打开这条 trace，看到每一步调用了哪个工具、耗时、token 和失败摘要。`--mock` 不产生费用，也不需要 `.env`。

### 常见坑

- PowerShell 不支持 `A && B`（7.0+ 才支持），用 `;` 或分两行。
- 不要激活 venv：`.venv\Scripts\Activate.ps1` 常被执行策略拦截（"在此系统上禁止运行脚本"），直接用 `.venv\Scripts\python.exe` 最稳。
- `--task` 是相对当前目录解析的，离开仓库目录要传绝对路径，例如 `--task D:/repopilot/eval/bugsets/bug_0001`。
- 必须能读到 `pyproject.toml`：请在仓库根目录执行，不要在 `eval/` 或 `src/` 子目录下跑。

## 3. 真实评测怎么跑

Windows PowerShell：

```powershell
Copy-Item .env.example .env
.venv\Scripts\python.exe eval/run_eval.py --model real --max-steps 12 --no-docker
```

Git Bash / macOS / Linux：

```bash
cp .env.example .env
.venv/bin/python eval/run_eval.py --model real --max-steps 12 --no-docker
```

然后编辑 `.env`，至少填：

```text
LLM_API_KEY / LLM_BASE_URL / LLM_MODEL
LLM_PRICE_IN_PER_1M / LLM_PRICE_OUT_PER_1M（元/百万 token；不填则成本显示 n/a）
```

`--no-docker` 表示用本机 subprocess 跑测试。要启用容器隔离，先构建镜像，再把 `--no-docker` 换成 `--docker`：

Windows PowerShell：

```powershell
docker build -f docker/Dockerfile -t repopilot-sandbox:pytest9 .
.venv\Scripts\python.exe eval/run_eval.py --model real --max-steps 12 --docker
```

Git Bash / macOS / Linux：

```bash
docker build -f docker/Dockerfile -t repopilot-sandbox:pytest9 .
.venv/bin/python eval/run_eval.py --model real --max-steps 12 --docker
```

容器参数是 `--network=none --memory=1g --cpus=1`，只挂载被测仓库目录。`--only <task_id>` 可以只跑单题，`--report-name` 指定报告文件名。

## 4. 评测结果

三次评测均为单次采样，不能当作模型能力上限；成本一栏是**按配置单价计算，单价待校准**。

| 难度 | 通过 | 平均轮数 | token / 题 | 成本 | 来源报告 |
|---|---|---|---|---|---|
| 自造基础 10 题（5 类注入 bug） | **10/10** | 3.2 | ~3,500 | 按配置单价计算，单价待校准 | `eval/reports/w2-summary-cost.md` |
| 自造跨文件难题 3 题 | **1/3** | 5（通过题）/ 7（全部） | 20,681 | 按配置单价计算，单价待校准 | `eval/reports/w3-hard.md` |
| 真实仓库 cachetools（反向注入 commit `2609f06`） | **0/1** | 12（撞步数上限） | prompt 123,088 / completion 2,223 | 按配置单价计算，单价待校准 | `eval/reports/w3-real-2.md` |

关键口径：

- 基础 10 题平均 3.2 轮、单题约 3,500 token，全部 `tests_passed`。
- 跨文件 3 题只过 1 题，2 题以 `max_steps` 结束；说明单文件题已经饱和，跨文件才拉开差距。
- 真实仓库题基于 cachetools HEAD `e7104dd`，把 bugfix commit `2609f06` 的源码 hunk 反向应用，测试保持 HEAD 版本；初始红色为 `18 failed, 369 passed`。
- 真实题第一次跑出过假阳性：harness 判 True，人工复核发现源码未改、测试仍红（`eval/reports/w3-real.md`）。加复核闸口后复跑结果为 0/1，即上表这一行。

## 5. 架构

```text
CLI：python -m repopilot run --task <dir> [--mock] [--docker]
                │
                ▼
        Agent Loop（步数熔断 + 同类错误熔断）
        ├─ 连续 2 次同类 ERROR → 注入针对性提醒
        └─ 连续 3 次同类 ERROR → 升级为整文件 write_file 策略
                │
                ├── read_file   带行号、按行区间读，单次最多 200 行
                ├── apply_patch unified diff；任一 hunk 失败则整批回滚
                ├── run_tests   返回 exit_code + 末 40 行；拦截 | ; && > 等 shell 元字符
                └── write_file  熔断升级后的兜底：整文件覆盖
                │
                ▼
        docker run --network=none --memory=1g --cpus=1
        （或 --no-docker：本机 subprocess）
                │
                ▼
        JSONL trace：每步一行（工具、参数摘要、耗时、tokens、breaker）
                │
                ▼
        复核闸口：模型命令返回 exit_code=0 后，用题目原始 test_cmd
        无条件复跑；仍红则判 false_positive_blocked，不算通过
```

3 个主工具加 1 个兜底工具；工具返回 ERROR 只回灌给模型，不中断循环。

## 6. 这个项目踩过的四个坑

**假阳性：`| tail` 吞掉 pytest 退出码。** 真实仓库题里模型执行 `pytest ... | tail -60`，管道退出码取最后一环 `tail`，harness 看到 0 就判通过，但 `src/` 和 `tests/` 一个字节没改。修法：`run_tests` 拦截 `| ; && >` 等元字符，并在判定通过后用题目原始 `test_cmd` 无条件复跑一次。

**同类错误反复重试导致 token 膨胀。** bug_0012 在 8 步里出现 6 次 ERROR，prompt 累计 31,709 token，模型反复提交同样的坏 diff 和绝对路径。修法：按 `classify_error` 把错误分成 format / path / other，连续 2 次注入具体格式或路径提醒，连续 3 次强制改用整文件写入；同一题 prompt 降到 21,283（约 −33%），但该题仍未通过——熔断省的是无效探索，不是把失败变成功。

**read_file 把仓库内绝对路径判成越界。** 模型传入 `D:\...\repo\stats.py` 这类仓库内绝对路径时被拒绝，白耗一轮。根因是安全校验拿原始路径和仓库根做前缀比较，没有先归一化。修法：先 `Path.resolve()`，再用 `root in target.parents` 判断真实越界，仓库内绝对路径统一转成相对路径。

**把通过错误归因于步数预算。** bug_0012 在 12 步配置下通过，最初结论是“8 步预算太紧”。但那次同时改了步数上限和路径归一化，两个变量混在一起。补了固定 8 步 + 路径修复的对照实验后，8 步也能通过（20,579 prompt），推翻了原先的归因：起作用的是路径修复，不是预算。

## 7. 已知限制

- 单进程串行：一题跑完再跑下一题，没有并发、没有任务队列。
- 只支持 Python + pytest/单测：不处理编译型语言、前端构建、多服务依赖。
- 上下文没有预算控制：每轮重发全部历史，真实仓库题 12 轮累计 prompt 达到 123,088 token，尚无摘要或裁剪机制。
- 成本单价仍是占位值：`.env` 不填单价时只报 token 和 `cost=n/a`，要得到可信金额必须先按厂商当期价格校准。
