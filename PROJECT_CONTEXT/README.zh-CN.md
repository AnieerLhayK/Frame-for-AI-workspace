# PROJECT_CONTEXT

`PROJECT_CONTEXT/` 是该工作空间的活跃任务记忆层。它为人类和兼容的维护型智能体提供了一种快速了解当前任务状态、活跃决策以及后续会话应如何继续工作的方式。

## 这是什么

- 活跃任务记忆层。
- 会话交接入口点。
- 当前状态摘要。
- 决策记录索引。
- 轻量级任务连续性台账。
- 未来工作的规划面。

## 这不是什么

- 不是机器可读的事实来源。事实来源仍然是 `workspace_manifest.yaml`。
- 不是架构或范围参考。架构参考现在是 `ARCHITECTURE.md`。
- 不是风格指南。风格指南现在是 `WORKSPACE_ENGINEERING/skill_engineering/style_alignment.md`。
- 不是协议索引。工作空间协议由 `shared/INDEX.md` 索引；包内协议由各包内部索引。
- 不是协议层。协议规则位于根目录或包内本地的 `shared/` 中。
- 不是生成的报告层。快照位于 `reports/` 中。
- 不是运行时事件台账。运行时漂移记录位于 `packages/character-system/reports/runtime-loop/` 中。
- 不是技能实现。

## 层关系

- `workspace_manifest.yaml`：机器可读的事实来源，包含根目录、技能角色、权限、执行模式、暴露范围、投影、协议和可移植性元数据。
- `shared/`：工作空间全局治理协议层。
- `packages/character-system/shared/`：角色系统协议层。
- `reports/`：快照层。
- `packages/character-system/reports/runtime-loop/`：持久化运行时事件跟踪层。
- `ARCHITECTURE.md`：工作空间范围和物理架构参考（取代原有的 `PROJECT_CONTEXT/architecture.md` 和 `PROJECT_CONTEXT/workspace_purpose.md`）。
- `PROJECT_CONTEXT/`：活跃任务记忆层（任务台账、注册表、状态、待办事项、会话交接）。
- `packages/`：按领域和生命周期角色组织的相关技能系列。
- `skills/`：不依赖包内业务协议的独立技能。
- `PROJECT_CONTEXT/task_registry.yaml`：任务路由层，在大范围发现之前限制所需上下文。
- `PROJECT_CONTEXT/context_budget.md`：上下文预算层，控制何时扩展超出必需文件的范围。
- `PROJECT_CONTEXT/task_ledger.md`：轻量级维护台账；在重建历史之前请先阅读最近的 5 条条目。
- `PROJECT_CONTEXT/change_surface_policy.md`：用于比较可替代可写文件集的决策规则。
- `PROJECT_CONTEXT/knowledge_registry.yaml`：当前上下文、可执行政策和可复用工程知识的主题索引。

## 新会话推荐阅读顺序

1. 阅读根目录 `ARCHITECTURE.md`（工作空间范围和物理架构）。
2. 阅读根目录 `AGENTS.md`（智能体启动说明）。
3. 运行 `git status --short --untracked-files=all`。
4. 如果任务 ID 未知，运行 `python scripts/resolve_task_context.py --list`。
5. 运行 `python scripts/resolve_task_context.py <task-id>`。
6. 仅阅读返回的必需文件。
7. 仅在连续性相关时阅读最近的任务台账条目。
8. 仅根据证据扩展可选上下文。
9. 当仍有多个合理的归属层时，运行 `python scripts/workspace_cli.py changes plan <task-id> --intent <intent>`。
10. 当需要的知识条目尚未被任务路由时，使用 `python scripts/workspace_cli.py knowledge find "<topic>"`。

## 最低维护工作流程

每次后续维护应执行：

1. 阅读项目上下文条目文件。
2. 检查 `git status --short`。
3. 通过 `workspace_manifest.yaml` 解析路径。
4. 使用 `scripts/resolve_task_context.py` 解析任务。
5. 在扩展上下文之前应用返回的令牌预算。
6. 在连续性相关时阅读最近的 `PROJECT_CONTEXT/task_ledger.md` 条目。
7. 先加载任务的必需上下文，再加载可选上下文。
8. 编辑最窄的归属层。
9. 运行相关的验证或试运行。
10. 当决策、风险、后续步骤或连续性发生变化时更新 PROJECT_CONTEXT。

添加新技能时，首先确定它属于现有领域技能、新包/领域、独立技能还是独立工作空间。不要将不相关的业务规则强行放入顶层 `shared/` 中。

## 什么情况下更新此处

在以下情况下更新 `PROJECT_CONTEXT/`：

- 治理阶段完成时；
- 做出重大架构决策时；
- 已知风险发生变化时；
- 添加新的验证层或运行循环时；
- 引入新的技能/包边界时；
- 未来会话需要清晰的交接上下文时。

## 不应放入的内容

不应放入：

- 复制的共享协议文本；
- 整篇粘贴的生成报告内容；
- 私有语料库材料；
- 本应属于 `packages/character-system/reports/runtime-loop/` 的运行时数据包实例；
- 本应属于清单文件或协议清单的机器可读注册表数据。

不要将 `PROJECT_CONTEXT/task_ledger.md` 用作报告或 Git 历史的替代品。它是有记录的决策索引，而不是证据本身。
