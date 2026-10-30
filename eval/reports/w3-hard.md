# W2 评测报告

- 运行时间：2026-10-31 00:12:41（run_id `20261031-001241`）
- 模型：`deepseek-flash`（mode=real）
- 沙箱：本机 subprocess（--no-docker）
- max_steps：8
- 单价：输入 0.04 / 输出 8.0（元/百万 token）

## 三个数字

- 通过数：**1/3**（33.3%）
- 平均轮数：**5**（通过题） / 7（全部题）
- 单题成本：**¥0.0238**（总成本 ¥0.0713）

- 总 token：62044（prompt 53393 / completion 8651），单题平均 20681.3

## 逐题明细

| task | ok | steps | prompt | completion | cost | duration(s) | reason | ERROR 步数 | tests 未改 |
|---|---|---|---|---|---|---|---|---|---|
| bug_0011 | True | 5 | 6706 | 396 | ¥0.0034 | 7.94 | tests_passed | 1 | True |
| bug_0012 | False | 8 | 31709 | 6454 | ¥0.0529 | 34.71 | max_steps | 6 | True |
| bug_0013 | False | 8 | 14978 | 1801 | ¥0.0150 | 14.57 | max_steps | 4 | True |

## 失败归因索引

- max_steps：bug_0012、bug_0013
- no_tool_calls_failed：无
- 有 ERROR 的题：bug_0011、bug_0012、bug_0013
- 改过测试的题（判为不通过）：无
