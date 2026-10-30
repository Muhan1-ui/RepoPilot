# 评测集约定

一题一个目录，放在 `eval/bugsets/`，目录名即 `task_id`：

```
eval/bugsets/
└── bug_0003/
    ├── meta.json          # id / category / description / test_cmd
    ├── repo_clean/        # 干净的初始快照（= 做题起点，测试此时必须是红的）
    │   ├── <module>.py
    │   ├── pytest.ini
    │   └── tests/test_<x>.py
    └── repo/              # 初始副本；每次评测前用 repo_clean 整体重置
```

`repo_clean` 是“起点快照”而不是“修好的版本”：它保留注入的 bug，评测时由 agent
自己修。`repo/` 由 `reset_repo()` 自动生成，不需要手工维护。

## 新题目录约定

- `meta.json` 必填 `id`、`description`、`test_cmd`（默认 `python -m pytest -q`）；
  `category` 仅用于报告归因。真实模型评测**不放** `mock_script.json`。
- 单模块、单文件 bug；题目代码 ≤ 40 行，不引入第三方依赖（pytest 由运行环境提供）。
- 每题 4~6 条测试，至少 2 条在初始状态失败；测试只断言行为，不改被测模块。
- `pytest.ini` 固定为：
  ```ini
  [pytest]
  testpaths = tests
  pythonpath = .
  ```

## 怎么判断“这道题是合法的”

1. **初始必红**：`.venv/Scripts/python.exe -m pytest eval/bugsets/<id>/repo_clean -q`
   退出码非 0，且 `failed >= 2`。
2. **修复后必绿**：在 repo_clean 的临时副本上应用预期修复（一行左右），pytest 退出码 0；
   同时 `tests/` 文件字节不变（防止靠改测试通过）。
3. **不考知识只考读码**：失败输出里能直接看到
   `FAILED tests/...::test_x`、断言差异（`assert 3 == 2.5`）和 `file:line`；
   模型只需读代码 + 跑一次测试就能定位，不依赖领域知识或外部资料。
4. **可复现**：无网络、无私有数据、无随机/时间依赖；同一命令重复跑结果一致。

`eval/run_eval.py` 会逐题 `reset_repo()`，因此任何一次真实评测都可以从同一初始状态重跑。

## 10 题覆盖

| 类别 | 题号 |
|---|---|
| off-by-one | bug_0002、bug_0007 |
| 边界条件（空/单元素/负数） | bug_0003、bug_0008 |
| 异常类型 / 未捕获 | bug_0004 |
| 类型转换（int/float/str、整除） | bug_0005、bug_0009 |
| 循环 / 短路条件写反 | bug_0006、bug_0010 |

另有 bug_0001（中位数，off-by-one 变体）作为 W1 的冒烟题。

## 跑评测

```bash
python eval/run_eval.py --model real --max-steps 8 --no-docker
python eval/run_eval.py --model real --max-steps 8 --no-docker --only bug_0003
```

报告落在 `eval/reports/w2-summary.json` 与 `eval/reports/w2-summary.md`；
每题轨迹在 `eval/bugsets/<id>/runs/<timestamp>/trace.jsonl`。
