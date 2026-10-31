# W2 评测报告

- 运行时间：2026-10-31 09:37:43（run_id `20261031-093743`）
- 模型：`deepseek-flash`（mode=real）
- 沙箱：docker（--network=none）
- max_steps：12
- 单价：输入 0.04 / 输出 8.0（元/百万 token）

## 三个数字

- 通过数：**0/1**（0.0%）
- 平均轮数：**n/a**（通过题） / 12（全部题）
- 单题成本：**¥0.0227**（总成本 ¥0.0227）

- 总 token：125311（prompt 123088 / completion 2223），单题平均 125311.0

## 逐题明细

| task | ok | steps | prompt | completion | cost | duration(s) | reason | ERROR 步数 | tests 未改 |
|---|---|---|---|---|---|---|---|---|---|
| real_0001 | False | 12 | 123088 | 2223 | ¥0.0227 | 37.20 | max_steps | 2 | True |

## 失败归因索引

- max_steps：real_0001
- no_tool_calls_failed：无
- 有 ERROR 的题：real_0001
- 改过测试的题（判为不通过）：无
