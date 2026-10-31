# W2 评测报告

- 运行时间：2026-10-31 00:42:18（run_id `20261031-004218`）
- 模型：`deepseek-flash`（mode=real）
- 沙箱：本机 subprocess（--no-docker）
- max_steps：8
- 单价：输入 0.04 / 输出 8.0（元/百万 token）

## 三个数字

- 通过数：**1/1**（100.0%）
- 平均轮数：**8**（通过题） / 8（全部题）
- 单题成本：**¥0.0281**（总成本 ¥0.0281）

- 总 token：23986（prompt 20579 / completion 3407），单题平均 23986.0

## 逐题明细

| task | ok | steps | prompt | completion | cost | duration(s) | reason | ERROR 步数 | tests 未改 |
|---|---|---|---|---|---|---|---|---|---|
| bug_0012 | True | 8 | 20579 | 3407 | ¥0.0281 | 21.72 | tests_passed | 3 | True |

## 失败归因索引

- max_steps：无
- no_tool_calls_failed：无
- 有 ERROR 的题：bug_0012
- 改过测试的题（判为不通过）：无
