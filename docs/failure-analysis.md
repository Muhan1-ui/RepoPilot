# W2 失败归因

## 结论

**10/10 通过（pass@1 = 100%，平均 3.4 轮，总 token 40770，成本 n/a）。**
本轮没有失败题，按约定附一条最强题的最短轨迹。

## 最强题：bug_0009（字符串类型转换，7 轮）

选它作为“最强”的依据：轮数 7（其余题为 3）、token 11761（其余约 3k）、
耗时 10.36s（其余 3.5~5.2s），且唯一一次工具 ERROR 出现在这题。

7 轮轨迹（`eval/bugsets/bug_0009/runs/20261030-235210/trace.jsonl`）：

1. `read_file pricing.py` + `read_file tests/test_pricing.py`：模型一次读源码和测试。
2. `apply_patch` → `OK`：把 `price * qty` 改成 `float(price) * float(qty)`，但同一个
   patch 里多带了不存在的尾部上下文。
3. `apply_patch` → `ERROR: hunk 1 failed: context mismatch in pricing.py near line 3`：
   模型试图再补一个 hunk，上下文对不上。
4. `read_file pricing.py`：重新读取真实内容（工具回灌没有中断循环）。
5. `apply_patch` → `OK`：按真实行号重写 hunk。
6. `read_file pricing.py`：确认文件形态。
7. `run_tests` → `exit_code=0`，通过。

归因（针对第 3 步的 ERROR）：**工具/环境侧**——`apply_patch` 的上下文校验按设计拒绝了
不匹配的 hunk，错误信息带 `file + line`，模型下一步读文件后自行恢复；不是模型没看懂，
也不是关键文件缺失。这类“先失败一次再恢复”的轨迹正是结构化观察应有的效果。

下次改什么：当前题集是单文件、单函数、失败信息直接给出 `file:line` 和断言差异，
难度偏低（7/10 题 3 轮即通过），pass@1 已饱和。W3 若继续用这套评测，应至少加一道
跨两个文件的题（例如调用方与被调用方各一处 bug），否则通过率无法区分模型强弱；
本轮数字更适合作为“闭环可用”的基线，而不是能力上限。

## real_0001（真实仓库，0/1）

数据来源：`eval/reports/w3-real-2.json`（run_id `20261031-093743`）与
`eval/bugsets/real_0001/runs/20261031-093743/trace.jsonl`（17 条记录 / 12 步）。
本次只做离线取证，未改判定逻辑、未重跑评测。

**卡在第几步。** 第 12 步（`reason=max_steps`，步数上限 12）。trace 里 12 步共
10 次 `read_file`、7 次 `run_tests`、**0 次 `apply_patch` / `write_file`**——模型
一直在读文件和跑测试，从未提交过修改。`tests_untouched=True` 只是“没改测试”，
同样也说明“没改源码”。

**最后一条工具返回的首行。** `exit_code=2`（step 12，cmd 为
`--tb=long tests/test_cachedmethod.py::CacheMethodTest::test_decorator_pickle`）。
离线复跑该命令得到 `sh: 0: Illegal option --`；step 11 的
`tests/test_cachedmethod.py::... -x --tb=long -q` 复跑为
`sh: 1: tests/...: not found`（exit 127）。两条命令都缺了 `python -m pytest` 前缀。

### 每步 prompt token

| step | 本步工具 | prompt | Δ | completion | 说明 |
|---|---|---|---|---|---|
| 1 | read_file(根目录) + run_tests(全量) | 800 | +800 | 75 | 读目录报错；全量 18 failed / 369 passed |
| 2 | run_tests + read_file(`__init__.py` 1-) | 1,093 | +293 | 101 | 带 `tail` 的管道命令被 shell 元字符拦截 |
| 3 | run_tests(单文件) + read_file(`__init__.py` 600-805) | 2,991 | +1,898 | 132 | 读 `__init__.py` 尾部 |
| 4 | read_file(`__init__.py` 780-805) + read_file(`_cachedmethod.py` 1-200) | 5,255 | +2,264 | 114 | 首次读 `_cachedmethod.py` |
| 5 | read_file(`_cachedmethod.py` 200-336) + read_file(`_descriptor.py` 全文件) | 7,422 | +2,167 | 114 | 读 descriptor 全文件 |
| 6 | read_file(`test_cachedmethod.py` 1-200) | 10,548 | **+3,126** | 88 | 本轨迹最大一次跳变 |
| 7 | run_tests(单用例) | 12,848 | +2,300 | 75 | 单用例仍失败 |
| 8 | read_file(`test_cachedmethod.py` 200-400) | 12,980 | +132 | 101 | 本步只读测试，下一跳在 step 9 |
| 9 | run_tests(单用例 `-x`) | 15,893 | +2,913 | 63 | 第二大的跳变 |
| 10 | read_file(`test_cachedmethod.py` 400-560) | 16,013 | +120 | 115 | 读测试尾部 |
| 11 | run_tests(裸 nodeid) | 18,161 | +2,148 | 866 | exit 127；本步 completion 异常大 |
| 12 | run_tests(`--tb=long ...`) | 19,084 | +923 | 379 | exit 2，随后撞 12 步上限 |

**增长形态是阶梯式近线性，不是指数跳变。** 每一步的增量基本等于“上一轮工具返回
+ 上一轮 completion”：读数落在 2k–3k 区间，只有上一轮返回很小时才出现 +132 / +120
这种小台阶。没有出现某一步突然翻倍。

**跳得最猛的一步是 step 6（+3,126 token）。** 它之前是 step 5 的两次 `read_file`：
`_cachedmethod.py` 200–336 行（137 行，5,292 字符）+ `_descriptor.py` 全文件
（161 行，6,575 字符），合计 11,867 字符，再加 step 5 的 114 completion。
单条最大的工具返回则出现在 step 8：`test_cachedmethod.py` 200–400 行，9,810 字符，
对应 step 9 的 +2,913。

**`feedback.py` 对 381 个测试回灌了多少。** step 1 的全量 `python -m pytest -q`
原始 stdout 是 18,057 字符（18 failed / 369 passed）；`format_pytest_failure`
实际返回 **367 字符**，**没有超过 800 字符上限**，也未被硬截断。它按
`max_failures=3` 只列 3 条 FAILED，末尾标注“另有 9 条未列出”（12 条 FAILED 行，
6 个 subtest 失败被折叠）。也就是说全量输出确实很大，但工具层已经把它压到很小。

**一句话结论。** 主要膨胀来自“每步重发全部历史”，不是“单条工具输出太大”：
12 次调用累计 123,088 prompt token，最后一步的完整上下文只有 19,084 token，
两者之差 104,004（84.5%）是对同一段历史的重复计费；而最大的单条工具返回
9,810 字符（约 2.5k token）只占累计 prompt 的约 2%。

### 归因

- **模型（主因）**：12 步内 0 次写操作。读完了 `__init__.py`、`_cachedmethod.py`、
  `_descriptor.py` 和测试文件，却始终没有 `apply_patch`，失败不是被“卡住”而是
  根本没进入修复阶段。
- **工具（放大因素）**：step 2 的 shell 元字符拦截文案写着“只传 pytest 参数……
  完整命令由 harness 拼接”，但 `run_tests` 实际把 `cmd` 原样交给 shell、并不拼接。
  step 11/12 模型按文案只传了 nodeid / pytest 参数，于是分别得到 127 和 2。
- **预算**：`max_steps=12` 是终止条件，不是根因；轨迹里没有任何一次修复尝试，
  放宽步数也不会自动产生 patch。
- **上下文**：不是原因。最终上下文 19,084 token，远未触及模型窗口；123k 是逐轮
  重发的累计值，不是单次上下文长度。

**下次改什么：** 让 `run_tests` 在 `cmd` 不以解释器开头时自动补上
`python -m pytest`（与报错文案保持一致），同时对“连续多步只有读操作、没有写操作”
的轨迹尽早提示，避免 12 步全部耗在只读探索上。
