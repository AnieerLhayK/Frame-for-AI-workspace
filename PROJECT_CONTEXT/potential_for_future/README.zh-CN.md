# Potential For Future

本目录保存需要长期记住、但尚未成为当前 todo 或强制规则的规划材料。

## 分类

- `optimization_options.yaml`：仍处于 candidate 或 active 状态的工作区、架构、工具或工作流优化项。
- `risk_register.yaml`：仍处于 candidate 或 observed 状态的结构性、暴露和迁移风险。
- `history/`：按上述两类拆分、受 Git 追踪的终态决策历史；它不是被忽略的备份，也不属于普通启动上下文。

这里的条目是检索入口，不是实施计划。只有在当前证据和范围得到确认后，才应将条目提升为任务路由、策略、活跃 todo 或源代码变更。

implemented/rejected 的优化项，以及 mitigated/accepted/retired 的风险必须迁入对应的 history 登记；保留原条目并添加 `archived_at` 与 `source_registry`。`scripts/validate_future_register.py` 会强制检查这一边界。

新增分类时，应同步更新本说明、英文 companion、`PROJECT_CONTEXT/knowledge/index.yaml` 以及需要发现它的任务路由规则。历史任务台账不会因为登记表迁移而重写。
