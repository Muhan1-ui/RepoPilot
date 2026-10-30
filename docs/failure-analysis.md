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
