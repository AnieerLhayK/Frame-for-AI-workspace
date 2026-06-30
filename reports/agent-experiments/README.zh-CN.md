# Agent 实验

此目录接受来自已批准的测试注册的有界、低风险 `record_write` 输出。

每个测试 agent 必须使用其自身精确的子目录：

```text
reports/agent-experiments/<agent-id>/
```

创建此目录并不激活 agent，也不授予 source、structural、platform 或 snapshot-report 写入权限。
