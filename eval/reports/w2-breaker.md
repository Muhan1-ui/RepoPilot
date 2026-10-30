# W2：bug_0012 repeat breaker 前后对照

- 改动后：run `20261031-002644`，`--model real --max-steps 8 --no-docker --only bug_0012`（与改动前同模型、同步数上限）
- 改动前：本机 `w3-hard`（run `20261031-001241`）、容器 `w2-summary-docker`（run `20261031-002141`）
- 单题、单次采样；按 `w2-docker-vs-host.md` 修正后的口径，单次差异只记录，不下因果结论。

| 项 | 改动前（两次） | 改动后 |
|---|---|---|
| ok / reason | False / max_steps（本机、容器各一次） | False / max_steps |
| steps | 8 | 8 |
| prompt token | 31,709（本机）/ 31,739（容器） | 21,283 |
| 成本 | ¥0.0529 / ¥0.0406 | ¥0.0248 |
| ERROR 步数 | 6（本机）/ 3（容器） | 4 |

- 熔断触发了 2 次：第 3 步 `path_repeat`（模型连续 2 次用绝对路径读文件），第 7 步 `format_repeat`（`malformed hunk body` / `context mismatch` 连续 2 次）；两次之后都紧跟一次成功工具调用，计数清零，因此没有累计到连续 3 次，`whole_file` 升级未触发。
- prompt token 从 31,709 / 31,739 降到 21,283（-32.9% / -33.0%），成本降到 ¥0.0248；但题目仍未通过（8 步 `max_steps`）：第 8 步 `apply_patch` 成功后已没有步数跑测试或改另一个文件。
- 判断：格式问题不是唯一主要矛盾。本次还多花了 2 步在绝对路径错误上，8 步预算在“读两个文件 + 两次失败 + 一次成功 patch”后耗尽；熔断明显减少了无效重试的 token，但没有改变 pass 结果。
