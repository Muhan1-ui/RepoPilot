# W2 评测报告

- 运行时间：2026-10-31 00:06:20（run_id `20261031-000620`）
- 模型：`deepseek-flash`（mode=real）
- 沙箱：本机 subprocess（--no-docker）
- max_steps：8
- 单价：输入 0.04 / 输出 8.0（元/百万 token）

## 三个数字

- 通过数：**10/10**（100.0%）
- 平均轮数：**3.2**（通过题） / 3.2（全部题）
- 单题成本：**¥0.0025**（总成本 ¥0.0249）

- 总 token：34909（prompt 31955 / completion 2954），单题平均 3490.9

## 逐题明细

| task | ok | steps | prompt | completion | cost | duration(s) | reason | ERROR 步数 | tests 未改 |
|---|---|---|---|---|---|---|---|---|---|
| bug_0001 | True | 3 | 2961 | 278 | ¥0.0023 | 5.26 | tests_passed | 0 | True |
| bug_0002 | True | 3 | 2877 | 275 | ¥0.0023 | 5.10 | tests_passed | 0 | True |
| bug_0003 | True | 3 | 2892 | 230 | ¥0.0020 | 4.59 | tests_passed | 0 | True |
| bug_0004 | True | 3 | 2742 | 214 | ¥0.0018 | 5.34 | tests_passed | 0 | True |
| bug_0005 | True | 3 | 2825 | 255 | ¥0.0022 | 4.83 | tests_passed | 0 | True |
| bug_0006 | True | 3 | 2827 | 249 | ¥0.0021 | 5.15 | tests_passed | 0 | True |
| bug_0007 | True | 5 | 6285 | 691 | ¥0.0058 | 9.01 | tests_passed | 0 | True |
| bug_0008 | True | 3 | 2922 | 257 | ¥0.0022 | 5.24 | tests_passed | 0 | True |
| bug_0009 | True | 3 | 2764 | 250 | ¥0.0021 | 5.33 | tests_passed | 0 | True |
| bug_0010 | True | 3 | 2860 | 255 | ¥0.0022 | 4.87 | tests_passed | 0 | True |

## 失败归因索引

- max_steps：无
- no_tool_calls_failed：无
- 有 ERROR 的题：无
- 改过测试的题（判为不通过）：无
