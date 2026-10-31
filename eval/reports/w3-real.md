# W3 真实仓库题报告：real_0001

## 题源与证据链

（以下信息抄自 `eval/bugsets/real_0001/PROVENANCE.md`，未重新编造。）

- 上游仓库：https://github.com/tkem/cachetools（实际克隆镜像 `https://gitee.com/mirrors/cachetools.git`）
- 底座 HEAD：`e7104dd52bfe0e3aced6f3439fb6ed4d9c8ff52a`（`Update copilot instructions and review.`）
- 注入的 bugfix commit：`2609f068f909197d46c1ad84083fb3b1226db3de`
  （`Fix #417: Re-enable pickling of objects with cached methods.`）
- 注入方式：`git archive HEAD` 得到 `repo_clean`，再把该 commit 的**非测试**源码 hunk 反向应用；测试文件保持 HEAD 版本（含回归测试）。另加 `pytest.ini` 适配 src-layout。

### 初始红色

```
18 failed, 369 passed, 1 warning, 10 subtests passed in 1.53s
```

代表性断言（一行）：

```
_pickle.PicklingError: Can't pickle <function Cached.get at 0x...>: it's not the same object as tests.test_cachedmethod.Cached.get when serializing dict item '__wrapped__' when serializing cachetools._descriptor._Unbound state
```

### 正向修复后

在 `repo_clean` 副本上正向应用原始 commit 的源码 patch，同一命令：

```
381 passed, 16 subtests passed in 0.93s
```

## 本次运行配置

- 命令：`eval/run_eval.py --model real --max-steps 12 --docker --only real_0001 --report-name w3-real`
- 模型：`deepseek-flash`；单价 输入 ¥0.04 / 输出 ¥8.0（每百万 token）
- 沙箱：docker `--network=none`，镜像 `repopilot-sandbox:pytest9`
- run_id：`20261031-004142`；trace：`eval/bugsets/real_0001/runs/20261031-004142/trace.jsonl`

## Agent 结果

| 口径 | ok | steps | prompt | completion | cost | reason | ERROR 步数 |
|---|---|---|---|---|---|---|---|
| harness 判定 | True | 9 | 76,479 | 2,487 | ¥0.0230 | tests_passed | 2 |
| 人工复核 | **False** | 9 | — | — | — | 源码未改，测试仍红 | — |

**这是一次假阳性。** 复核证据：

1. `diff -rq repo_clean repo` 只有 `.pytest_cache` 差异，`src/` 与 `tests/` 逐字节未变（`tests_untouched=True` 也说明没有改测试，但同样说明没有改源码）。
2. 在该 `repo` 上直接跑 `python -m pytest -q`：`18 failed, 369 passed`，与初始红色完全一致。
3. 第 9 步 `run_tests` 的命令是：

```
python -m pytest -q tests/test_cachedmethod.py -k "pickle or deepcopy" 2>&1 | tail -60
```

   这条命令实际输出 `16 failed, 1 passed, 62 deselected`，但 shell 的退出码取管道最后一环 `tail`，为 **0**。harness 的 `run_tests` 用 `shell=True`（docker 下是 `sh -lc`）执行并直接信任 `p.returncode`，于是把失败当成了成功并立即 `break`。

## trace 前 6 步（工具名 + 结果首行）

| step | 工具 | 结果首行 | 说明 |
|---|---|---|---|
| 1 | read_file | `ERROR: . 是目录，请给出具体文件路径…` | 模型把仓库根当文件读，路径提示正常 |
| 1 | run_tests | `exit_code=1` | 全量测试，18 failed，符合预期 |
| 2 | read_file | `1|import unittest` | 读 `tests/test_cachedmethod.py` |
| 2 | read_file | `1|[build-system]` | 读 `pyproject.toml`，确认 src-layout |
| 3 | read_file | `ERROR: src/cachetools 是目录…` | 又一次把目录当文件 |
| 4 | read_file | `1|"""Extensible memoizing collections and decorators."""` | 读 `src/cachetools/__init__.py` |
| 4 | read_file | `1|"""Method decorator helpers."""` | 读 `src/cachetools/_cachedmethod.py` |
| 5 | read_file | `1|"""Descriptor helpers."""` | 读 `src/cachetools/_descriptor.py` |
| 5 | read_file | `200|                try:` | 读 `_cachedmethod.py` 200–336 行 |
| 6 | read_file | `200|        # assert hits/misses are counted per instance` | 读测试 200–460 行 |

到第 8 步为止模型**一次 `apply_patch` / `write_file` 都没调用**，第 9 步直接用带 `tail` 的过滤命令"验证"，被管道退出码骗过，循环提前结束。

## 归因（四类之一）

**工具。** 直接原因不是模型、上下文或预算，而是 `run_tests` 的工具语义：它允许模型提交任意 shell 命令串，并以最终进程退出码作为唯一判据；`cmd | tail`、`cmd; true` 这类写法会把 pytest 的失败码覆盖成 0。模型在拿到 `exit_code=0` 后没有机会再解释输出，harness 直接判定通过。

次要观察：前 8 步全部用于读文件，说明这题对"先读后改"的探索开销确实高；但即便这条命令没有管道，模型也会看到 16 failed 并继续，是否能在第 12 步前改对属于另一个问题。

**下次改什么：** 在 `run_tests` 层禁止或剥离会吞退出码的 shell 构造（至少对 `|`、`;`、`&&` 做拦截，或统一用 `set -o pipefail`；更稳的是只接受 pytest 参数、由 harness 自己拼命令），并在判定通过时用题目原始 `test_cmd` 复跑一次全量测试。

## 这题为什么比自造题难

- 初始就有 381 个测试、18 个失败，一次 `-q` 的输出规模远大于自造题（11 个测试），模型必须自己从长输出里定位到 `test_cachedmethod` 这一簇。
- 采用 src-layout（`src/cachetools/`），且 bug 横跨 `_cachedmethod.py` 与 `_descriptor.py`，模型不能靠猜根目录文件名命中。
- 失败语义是 pickle / `copy.deepcopy` 的对象身份与 `__wrapped__` 序列化，需要理解 descriptor 的 `__reduce__` 行为，而不是改一个边界条件。
