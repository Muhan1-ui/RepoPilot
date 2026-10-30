# W2 评测报告

- 运行时间：2026-10-30 23:52:10（run_id `20261030-235210`）
- 模型：`deepseek-flash`（mode=real）
- 沙箱：本机 subprocess（--no-docker）
- max_steps：8
- 单价：输入 未配置（cost=n/a） / 输出 未配置（cost=n/a）（元/百万 token）

## 三个数字

- 通过数：**10/10**（100.0%）
- 平均轮数：**3.4**（通过题） / 3.4（全部题）
- 单题成本：**n/a**（总成本 n/a）

- 总 token：40770（prompt 36871 / completion 3899），单题平均 4077.0

## 逐题明细

| task | ok | steps | prompt | completion | cost | duration(s) | reason | ERROR 步数 | tests 未改 |
|---|---|---|---|---|---|---|---|---|---|
| bug_0001 | True | 3 | 2944 | 261 | n/a | 4.28 | tests_passed | 0 | True |
| bug_0002 | True | 3 | 2906 | 302 | n/a | 4.62 | tests_passed | 0 | True |
| bug_0003 | True | 3 | 2911 | 249 | n/a | 4.35 | tests_passed | 0 | True |
| bug_0004 | True | 3 | 2793 | 264 | n/a | 4.11 | tests_passed | 0 | True |
| bug_0005 | True | 3 | 3133 | 561 | n/a | 5.23 | tests_passed | 0 | True |
| bug_0006 | True | 3 | 2815 | 236 | n/a | 4.38 | tests_passed | 0 | True |
| bug_0007 | True | 3 | 3007 | 342 | n/a | 4.39 | tests_passed | 0 | True |
| bug_0008 | True | 3 | 2938 | 273 | n/a | 3.80 | tests_passed | 0 | True |
| bug_0009 | True | 7 | 10584 | 1177 | n/a | 10.36 | tests_passed | 1 | True |
| bug_0010 | True | 3 | 2840 | 234 | n/a | 3.51 | tests_passed | 0 | True |

## 失败归因索引

- max_steps：无
- no_tool_calls_failed：无
- 有 ERROR 的题：bug_0009
- 改过测试的题（判为不通过）：无
