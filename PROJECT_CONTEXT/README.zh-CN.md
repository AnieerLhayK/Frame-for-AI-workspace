# PROJECT_CONTEXT

`PROJECT_CONTEXT/` 是 workspace 的活跃任务记忆层，记录当前状态、决策、连续性和未来工作；
它不是路径、协议或生成报告的事实来源。

## 权威层次

- `workspace_manifest.yaml`：机器可读的根目录、角色、权限、暴露、投影、协议和可移植性事实；
- `ARCHITECTURE.md`：workspace 范围与物理布局；
- `shared/`：工作区级可执行协议；
- `packages/character-system/shared/`：包内协议；
- `reports/`：生成或编写的快照；
- `packages/character-system/reports/runtime-loop/`：运行时诊断记录；
- `PROJECT_CONTEXT/`：活跃记忆。

## 内容

- `current_status.md`：最新核验状态、开放风险和近期验证；
- `decisions.md`：长期架构与治理决策；
- `task_registry.yaml`：任务路由和写入范围；
- `task_records/`：机器可读任务结果；
- `task_ledger/`：按日期记录的轻量连续性索引；
- `todo/`：活跃待办和接收队列；
- `knowledge_registry.yaml`：可复用知识的有界主题索引；
- `doc_pair_registry.yaml`：Markdown 伴侣覆盖规则；
- `change_surface_policy.md`：可替代写入面的比较规则；
- `potential_for_future/`：尚未激活的风险和优化选项。

## 新会话流程

1. 阅读根 `AGENTS.md`，运行 `git status --short --untracked-files=all`；
2. 用 `scripts/resolve_task_context.py` 解析精确任务；
3. 先读取解析器返回的必需上下文，再扩大搜索；
4. 在 workspace 或外部写入前启动任务记录；
5. 编辑最窄的源码归属层，路径以 manifest 为准；
6. 在记录有效期间运行路由验证和 `workspace workflow check`；
7. 只有状态、决策、风险或连续性发生变化时才更新此层。

有登记伴侣的 Markdown 应语义同步已有 `.zh-CN.md`。缺失伴侣作为例外记录，不自动新增文件。

## 不应放入

不要复制共享策略、整篇生成报告、私有语料、运行时数据包实例或 manifest/协议机器数据。
不要把 `task_ledger/` 当作报告或 Git 历史的替代品。
