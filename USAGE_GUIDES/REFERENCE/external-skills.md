# 外来技能使用指南

这是一份面向人工查阅的外来技能目录。它只覆盖 `external-skills/` 下已适配、已登记的技能；不包含 `skills/` 或 `packages/` 中 Workspace 自有技能。技能集合、调用策略、权限和平台暴露以 `workspace_manifest.yaml` 与各 `SKILL.md` 为准；本页帮助你选路，不取代它们。

## 先选路线

| 你现在的问题 | 首选技能 | 下一步常见去向 |
| --- | --- | --- |
| 想法模糊，担心一开始就做错 | `$grill-me` 或 `$grill-with-docs` | `to-spec` |
| 方案已明确，需要可执行的本地计划 | `to-spec` | `to-tickets` |
| 要把一个行为可靠地做出来 | `tdd` | `code-review` |
| 行为异常、回归或变慢 | `diagnosing-bugs` | `tdd`、`code-review` |
| 跨会话推进多项依赖工作 | `$wayfinder` | `triage`、`handoff` |
| 一个事实必须经得住追问 | `research` | `prototype` 或 `to-spec` |
| 想系统掌握一种能力 | `$teach` | 课程中的练习与复盘 |

## 调用规则

- **可发现**：直接描述任务即可，例如“诊断这个回归”。也可显式写技能名。
- **显式调用**：必须写成 `$skill-name`。通常是因为该流程需要你主动选择，或可能涉及长流程、持久状态、实验文件或 Git 状态。
- **暴露**表示某平台能发现该技能，**不表示写权限**。PLAN/MAP、课程文件、staging 原型和 Git 操作仍分别需要确认与活动 TASK record。
- 下面的“短调用”是方便启动的句子，不是 prompt registry 的独立模板。

## Productivity：澄清、交接与工作节奏

### `grill-me`

- **价值/适用**：用连续追问把一个想法打磨成可判断的计划；没有仓库或不想留下正式文档时最合适。
- **边界**：需要把已确认决定沉淀进仓库时改用 `$grill-with-docs`；只是一次普通澄清可直接对话。
- **暴露/调用**：Codex、Claude；显式。短调用：`$grill-me 我想验证一个新方案，但目标和取舍还不清楚。`
- **经典场景**：在投入数周开发前，逼问“谁受益、如何失败、何时算成功”。**项目映射**：非 Git Agent 项目的早期方向选择。

### `grilling`

- **价值/适用**：一问一答的压力测试原语；适合其他流程中出现关键假设时。
- **边界**：若需要完整路线和文件化决定，使用 `grill-with-docs`。
- **暴露/调用**：Codex、Claude；可发现。短调用：`请用 grilling 检验这个数据处理假设。`
- **经典场景**：追问“这个指标为什么代表成功”。**项目映射**：Git 数模仓库的模型选择前提。

### `handoff`

- **价值/适用**：把当前上下文压缩为下一位 agent、下一任务或另一工具可接手的说明。
- **边界**：不是长期项目规划器；跨会话依赖图使用 `$wayfinder`。
- **暴露/调用**：Codex、Claude；显式。短调用：`$handoff 把当前实验复现工作交给下一次会话。`
- **经典场景**：保留已验证结论、未决问题和下一步。**项目映射**：Workspace 维护任务的阶段交接。

### `i-have-adhd-local`

- **价值/适用**：让输出持续采用“下一动作优先、短步骤、可见进展”的节奏。
- **边界**：它改变沟通形式，不替代规划、诊断或执行技能。
- **暴露/调用**：Codex、OpenCode；显式。短调用：`$i-have-adhd-local，帮我把这项工作拆成短回合。`
- **经典场景**：长任务中保持方向和状态感。**项目映射**：任何持续推进的 Workspace 维护工作。

## Engineering：设计、计划、实现与验证

### `ask-matt`

- **价值/适用**：当你不知道该选哪个已安装流程时做路由建议。
- **边界**：它不替你启动必须显式调用的技能，也不替代实际工作。
- **暴露/调用**：Codex、Claude；可发现。短调用：`ask-matt：我需要把一个已讨论的功能变成可执行工作。`
- **经典场景**：从模糊意图选出第一步。**项目映射**：Workspace 自身的技能/治理改动。

### `to-spec` / `to-tickets`

- **价值/适用**：前者把已谈清的需求变为本地 spec PLAN；后者把确认的 PLAN 拆成可独立验证、依赖正确的 ticket PLAN。
- **边界**：两者先在对话展示草案，得到明确确认和活动 TASK record 后才持久化；不会创建外部 issue tracker 条目。
- **暴露/调用**：均为 Codex、Claude；可发现。短调用：`把刚才确定的实验可复现性改造整理为 spec。` / `把 PLAN-... 拆成可验证的 tickets。`
- **经典场景**：从“想做”变为可执行、可验收的垂直切片。**项目映射**：Git 数模仓库的功能或实验管线改造。

### `triage` / `wayfinder`

- **价值/适用**：`triage` 审核 PLAN 的证据、验收和阻塞；`$wayfinder` 管理跨会话 MAP、依赖前沿、决策与 24 小时认领。
- **边界**：不访问外部 tracker；PLAN/MAP 协调工作但不授予源码、Git 或外部写权限。
- **暴露/调用**：均为 Codex、Claude；`triage` 可发现，`wayfinder` 显式。短调用：`检查 PLAN-... 是否已有足够完成证据。` / `$wayfinder 更新这个长期目标的前沿。`
- **经典场景**：一边避免“已完成”的自我误判，一边让多项依赖工作不丢失。**项目映射**：Workspace 自身的分批迁移或长期工程改造。

### `tdd` / `diagnosing-bugs` / `code-review`

- **价值/适用**：`tdd` 用红绿重构交付一个具体行为；`diagnosing-bugs` 先定位故障根因；`code-review` 分别按仓库标准和原始规格审查变更。
- **边界**：诊断不是修复，审查不是实现；先有可复现症状或固定审查基点再启动最有效。
- **暴露/调用**：均为 Codex、Claude；可发现。短调用：`为这个输入校验新增测试并实现。` / `诊断同一实验两次结果不同。` / `审查从 main 到当前分支的变更。`
- **经典场景**：把“能跑”升级为“可复现、可解释、符合目标”。**项目映射**：Git 数模仓库的计算行为与回归控制。

### `codebase-design` / `improve-codebase-architecture`

- **价值/适用**：前者设计更深的模块边界与接口；后者扫描指定范围，输出架构改进报告。
- **边界**：架构扫描只产生 staging 报告，不直接改生产源码；术语/决策需要时交给 `domain-modeling`。
- **暴露/调用**：`codebase-design` 为 Codex、Claude且可发现；`improve-codebase-architecture` 仅 Codex且可发现。短调用：`为求解器和报告生成器选择模块边界。` / `评估该仓库的架构深化机会。`
- **经典场景**：从“大脚本”迁移到职责清晰的模块。**项目映射**：非 Git Agent 项目或 Git 数模仓库的结构整理。

### `domain-modeling` / `grill-with-docs`

- **价值/适用**：前者统一术语、更新词汇表或 ADR；后者通过追问收敛方案并保存已决定的术语/决定。
- **边界**：文档持久化仍要经过写授权；不把讨论中的猜测当成已决事实。
- **暴露/调用**：`domain-modeling` 可发现，`grill-with-docs` 显式；均为 Codex、Claude。短调用：`统一“episode”和“rollout”的项目定义。` / `$grill-with-docs 审视这项实验协议并保存确认的决定。`
- **经典场景**：让代码、实验记录和讨论使用同一套词。**项目映射**：非 Git Agent 项目的研究概念治理。

### `prototype` / `resolving-merge-conflicts`

- **价值/适用**：`$prototype` 用最小可丢弃实验验证高风险假设；`$resolving-merge-conflicts` 解释 merge/rebase 两侧意图并给出安全选项。
- **边界**：原型只能在受治理 staging 或隔离 worktree；冲突技能不会自动暂存、提交、continue 或 abort。
- **暴露/调用**：均仅 Codex、均显式。短调用：`$prototype 验证该算法在目标规模下是否可行。` / `$resolving-merge-conflicts 先解释这三个冲突双方想保留什么。`
- **经典场景**：先用事实减少大改风险；或在冲突中保留两侧真实意图。**项目映射**：Git 数模仓库的算法试验与分支整合。

### `writing-great-skills`

- **价值/适用**：检查 skill 指令的触发词、信息层级、重复、膨胀和完成标准。
- **边界**：它是 skill 写作质量参考；一般 agent 文档改写优先用 `writing-for-agents`。
- **暴露/调用**：Codex、Claude；显式。短调用：`$writing-great-skills 审阅这个 skill 是否存在重复和模糊触发条件。`
- **经典场景**：新增或重构技能之前压缩规则并消除歧义。**项目映射**：Workspace 自身的外来技能适配。

## Content：研究、学习与 agent 指令

### `research`

- **价值/适用**：用一手资料回答范围明确、需要可审计证据的问题。
- **边界**：不是开放式漫游；先界定结论要支持的主张。
- **暴露/调用**：Codex、Claude；可发现。短调用：`研究这个基准的官方评测协议是否允许该数据划分。`
- **经典场景**：把“我记得如此”替换为可核查来源。**项目映射**：非 Git Agent 项目的论文、基准和 API 事实核验。

### `teach`

- **价值/适用**：建立跨会话、目标驱动的课程，包含任务、资源、课次、练习和学习记录。
- **边界**：先选定主题；课程状态只有在明确授权及活动 TASK record 后才写入其 `courses/` 根；不改项目源码。
- **暴露/调用**：Codex、Claude；显式。短调用：`$teach 我想系统掌握可复现实验工程，并在四周内完成一个可验收项目。`
- **经典场景**：将零散学习转成有退出标准的长期训练。**项目映射**：Git 数模仓库的可复现研究能力建设。

### `writing-for-agents`

- **价值/适用**：编写或修订 agent 消费的说明、技能、`AGENTS.md`、上下文指针和完成标准。
- **边界**：不应复制 manifest 或协议的事实；应指向已有权威来源。
- **暴露/调用**：Codex、Claude；可发现。短调用：`重写这份 AGENTS.md，使权限边界和完成证据可执行。`
- **经典场景**：把“看起来像说明”的文档改为可预测的 agent 流程。**项目映射**：Workspace 自身的治理与使用指南维护。

## 高频组合

1. **规划到验收**：`to-spec -> to-tickets -> tdd -> code-review -> triage`。
2. **高风险研究想法**：`research -> $prototype -> $grill-with-docs -> domain-modeling`。
3. **故障到回归保护**：`diagnosing-bugs -> tdd -> code-review`。
4. **跨会话推进**：`handoff -> $wayfinder`。

## 维护与安全边界

- 新增、移除、改名外来技能，或改变其调用策略、authority、execution mode、平台 exposure 时，必须在同一变更中更新本页和两处入口 README。
- 不创建第二份机器可读 registry；任何“当前已暴露”事实都回查 manifest。
- `to-spec`、`to-tickets`、`triage`、`wayfinder` 使用本地 PLAN/MAP，不写外部 tracker。
- 原型产物属于 staging/隔离 worktree；课程状态属于 `teach` 的课程根；Git 冲突的 stage、commit、continue、abort 都必须另行确认。
