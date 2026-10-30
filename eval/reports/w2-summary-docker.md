# W2 评测报告

- 运行时间：2026-10-31 00:21:41（run_id `20261031-002141`）
- 模型：`deepseek-flash`（mode=real）
- 沙箱：docker（--network=none）
- max_steps：8
- 单价：输入 0.04 / 输出 8.0（元/百万 token）

## 三个数字

- 通过数：**12/13**（92.3%）
- 平均轮数：**3.67**（通过题） / 4（全部题）
- 单题成本：**¥0.0067**（总成本 ¥0.0874）

- 总 token：96690（prompt 86194 / completion 10496），单题平均 7437.7

## 逐题明细

| task | ok | steps | prompt | completion | cost | duration(s) | reason | ERROR 步数 | tests 未改 |
|---|---|---|---|---|---|---|---|---|---|
| bug_0001 | True | 3 | 2955 | 289 | ¥0.0024 | 6.06 | tests_passed | 0 | True |
| bug_0002 | True | 3 | 2931 | 327 | ¥0.0027 | 5.29 | tests_passed | 0 | True |
| bug_0003 | True | 3 | 2945 | 280 | ¥0.0024 | 5.92 | tests_passed | 0 | True |
| bug_0004 | True | 3 | 2817 | 284 | ¥0.0024 | 5.23 | tests_passed | 0 | True |
| bug_0005 | True | 3 | 2812 | 242 | ¥0.0020 | 4.97 | tests_passed | 0 | True |
| bug_0006 | True | 3 | 2844 | 260 | ¥0.0022 | 5.85 | tests_passed | 0 | True |
| bug_0007 | True | 3 | 3034 | 365 | ¥0.0030 | 5.57 | tests_passed | 0 | True |
| bug_0008 | True | 3 | 2955 | 285 | ¥0.0024 | 5.72 | tests_passed | 0 | True |
| bug_0009 | True | 4 | 4668 | 851 | ¥0.0070 | 8.09 | tests_passed | 1 | True |
| bug_0010 | True | 3 | 2889 | 278 | ¥0.0023 | 5.27 | tests_passed | 0 | True |
| bug_0011 | True | 6 | 7852 | 604 | ¥0.0051 | 10.97 | tests_passed | 1 | True |
| bug_0012 | False | 8 | 31739 | 4912 | ¥0.0406 | 28.70 | max_steps | 3 | True |
| bug_0013 | True | 7 | 15753 | 1519 | ¥0.0128 | 17.18 | tests_passed | 1 | True |

## 失败归因索引

- max_steps：bug_0012
- no_tool_calls_failed：无
- 有 ERROR 的题：bug_0009、bug_0011、bug_0012、bug_0013
- 改过测试的题（判为不通过）：无
