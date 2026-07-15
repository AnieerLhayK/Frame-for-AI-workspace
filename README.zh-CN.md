# Agent Ecosystem Workspace（智能体生态系统工作空间）

[English](README.md)

本工作空间以 `workspace_manifest.yaml` 为事实来源，统一管理技能根目录、角色、权限、执行模式、共享协议和平台映射。

## 项目上下文

新的人类或智能体会话应从 `ARCHITECTURE.md` 开始，然后阅读 `PROJECT_CONTEXT/README.md`、`PROJECT_CONTEXT/current_status.md` 和 `PROJECT_CONTEXT/todo.md`。

`PROJECT_CONTEXT/` 是活跃任务记忆层（任务台账、注册表、状态、待办事项）。它为当前工作提供方向，但不取代 `workspace_manifest.yaml`、`ARCHITECTURE.md`、`shared/`、`reports/` 或 `packages/character-system/reports/runtime-loop/`。

本工作空间是一个受管制的技能单体仓库（monorepo），而非单个巨型的智能体。在添加新技能之前，请判断它应归属于现有的包/领域、新的包/领域、独立的技能区域，还是独立的工作空间。不要将无关的业务规则强行放入顶层 `shared/`。

平台加载不等于能力所有权。同一源技能可以暴露给多个兼容平台，而无需改变其角色或权限。

## Claude Code 项目边界

Claude Code 使用其启动目录作为项目根目录。本工作空间通过根目录 `CLAUDE.md` 和追踪的 `.claude/` 规则注册为受管制的技能工作空间；它不是无关业务项目的容器。

请使用以下显式启动器：

```powershell
claude-workspace
claude-cnn
claude-ztemp
claude-project <alias>
```

你也可以直接 `cd` 到目标 Git 根目录后运行 `claude`。不要在一个已运行的 Claude 会话内部切换仓库；请从目标仓库重新启动 Claude，以确保原生编辑工具加载正确的防护。

CNN 仓库是一个独立的 Git 项目，通过机器本地的 Claude 项目注册表选择。它有意不在 `workspace_manifest.yaml` 中注册，因为该 manifest 管理的是工作空间技能和平台映射，而非外部的 Claude Code 项目。

## 技能工程知识

`WORKSPACE_ENGINEERING/` 是可复用的 AI 工作空间工程知识库。涵盖架构、智能体治理、可移植性、任务/上下文路由、运维经验以及作为子领域的技能工程。它不是当前项目状态，也不是可强制执行的协议层。

使用 `PROJECT_CONTEXT/` 了解本工作空间的当前状态。在设计未来的工作空间、技能、智能体治理或可复用维护模式时，使用 `WORKSPACE_ENGINEERING/`。

## 使用指南

`USAGE_GUIDES/` 是以提示词优先的使用层。当你需要即用型提示词、面向角色的技能参考以及平台特定的加载说明时，请打开它。

## 最低维护工作流

使用以下基线进行日常维护：

1. 检查 `git status --short`。
2. 需要时使用 `python scripts/resolve_task_context.py --list` 列出任务 ID。
3. 使用 `python scripts/resolve_task_context.py <task-id>` 解析任务。
4. 仅读取返回的必需上下文。
5. 编辑最窄的属主层。
6. 运行返回的验证命令。
7. 当长期决策、风险或下一步计划发生变化时更新 `PROJECT_CONTEXT`。
8. 在接到明确确认前不要提交，除非用户要求提交。

## 上下文解析器

解析器将任务注册表、提示词注册表和 token 预算整合在一起，无需写入文件：

```powershell
python scripts\resolve_task_context.py --list
python scripts\resolve_task_context.py --list-prompts
python scripts\resolve_task_context.py platform_exposure
python scripts\resolve_task_context.py skill_metadata_update --bind target-skill=packages/character-system/engineering/generation/character-generator
python scripts\resolve_task_context.py runtime_drift_fix --bind target-character=packages/character-system/runtime/characters/zyc --include-optional
python scripts\resolve_task_context.py --prompt-id zyc_natural_discussion --include-template
```

当注册表路径包含锚点时，直接提示词解析仅提取请求的 Markdown 章节。使用 `--format json` 进行智能体或脚本集成。安装 `scripts/requirements-context-tools.txt` 以获取精确的 `o200k_base` token 计数；否则，解析器使用清晰标注的启发式方法。

统一的开发者 CLI 是现有解析器和工作空间工具的轻量入口点：

```powershell
python scripts\workspace_cli.py task list
python scripts\workspace_cli.py task resolve platform_exposure
python scripts\workspace_cli.py prompt list
python scripts\workspace_cli.py prompt show task_routing --format json
python scripts\workspace_cli.py preflight skill_metadata_update --bind target-skill=packages/character-system/engineering/generation/character-generator
python scripts\workspace_cli.py bootstrap --print-json
python scripts\workspace_cli.py health
python scripts\workspace_cli.py health --with-tests
python scripts\workspace_cli.py summary
python scripts\workspace_cli.py summary --format json
python scripts\workspace_cli.py sessions audit
python scripts\workspace_cli.py sessions audit --migration-id character-package-20260614 --format json
python scripts\workspace_cli.py agent status
python scripts\workspace_cli.py agent check --agent hermes --path workspace_manifest.yaml
python scripts\workspace_cli.py agent request --agent hermes --mode review_only --summary "Register a missing skill" --path workspace_manifest.yaml
python scripts\workspace_cli.py skill list
python scripts\workspace_cli.py skill validate character-generator
python scripts\workspace_cli.py skill expose character-generator --platform codex
python scripts\workspace_cli.py launcher install
python scripts\workspace_cli.py failure check skill_metadata_update --bind target-skill=packages/character-system/engineering/generation/character-generator
python scripts\workspace_cli.py validate links
python scripts\workspace_cli.py reports status
python scripts\workspace_cli.py reports status --strict --format json
python scripts\workspace_cli.py reports refresh workspace
python scripts\workspace_cli.py changes plan developer_interface_tooling --intent tooling
python scripts\workspace_cli.py changes plan skill_metadata_update --intent metadata --bind target-skill=packages/character-system/engineering/generation/character-generator
python scripts\workspace_cli.py knowledge list
python scripts\workspace_cli.py knowledge validate
python scripts\workspace_cli.py knowledge find "skill 开发"
python scripts\workspace_cli.py knowledge find "工程现状" --layer project_context
```

`preflight` 使用严格的 token 预算执行。`reports status` 和 `validate links` 为只读操作。报告刷新是显式的；`validate manifest`、`validate protocols` 和 `reports refresh` 保留现有生成器的快照写入行为。

`sessions audit` 也是只读操作。它验证 manifest 声明的 Claude Code 和 OpenCode 存储、迁移备份、可移植导出以及记录的会话 ID 在源路径移动后是否仍然可恢复。

变更面规划也是只读操作。它根据明确的意图对已解析任务的可写层进行排序。要比较具体的备选方案，请重复使用 `--option NAME=PATH1,PATH2`；解析后的写入范围之外的选项、映射路径和仅报告替代项在排序前会被阻止。

知识查找由注册表支持且为只读操作。它返回条目路径和用途，无需搜索或加载每个索引文件。注册表是一个路由索引；manifest、共享策略、源文件和当前 Git 状态保留其现有权威性。

智能体治理由策略支持。它区分技能调用与工作空间修改、对目标路径进行分类，并将被拒绝的结构性工作路由为可审查的请求。它不验证智能体身份、不自动颁发租约、不创建工作树、不合并分支，也不编辑平台注册表。

资源强制遵循 `workspace_manifest.yaml -> failure_policy`：

- 缺少必需或预加载的上下文时返回整体状态 `ERROR` 和退出码 `1`；
- 仅在展开可选上下文时，缺少可选上下文才报告为 `WARNING`；
- JSON 输出暴露 `context.resource_findings`、整体 `status` 和独立的 `token_budget.budget_status`；
- 未解决的必需、写入范围或验证占位符将停止解析，而不会触发路径猜测。

启动上下文回归检查：

```powershell
python -m unittest scripts.tests.test_startup_context_policy
```

## 共享协议验证

角色系统协议层已在 `packages/character-system/shared/protocol_manifest.json` 中注册。

在修改 `shared/`、运行时循环模板、台账或任何核心技能的 `SHARED_PROTOCOLS.md` 文件后运行此检查：

```powershell
python scripts\validate_protocols.py
```

验证器会写入 `reports/protocol_validation_report.md`。该报告是一个快照；事实来源仍然是 `workspace_manifest.yaml`、`packages/character-system/shared/protocol_manifest.json`、`shared/` 和当前 Git 状态。

## 可移植性检查

工作空间的发现范围是受限的。工具应通过从已知起始路径向上寻找来找到 `workspace_manifest.yaml`，切勿扫描整个驱动器。

在移动工作空间、共享根目录、平台映射根目录或驱动器号之前，请运行：

```powershell
python scripts\bootstrap_workspace.py
python scripts\validate_manifest.py
python scripts\migration_dry_run.py --scenario root-rename --new-root <new-workspace-root>
python scripts\validate_protocols.py
powershell -ExecutionPolicy Bypass -File scripts\check_links.ps1
```

平台映射根目录可能保持为绝对路径，因为它们是本地部署入口点。工作空间内部的源路径应在可能的情况下保持相对于工作空间。

## 持续集成

GitHub Actions 在每次推送和拉取请求时运行基础 Python CI 工作流，也可以从 Actions 标签页手动启动。

该工作流安装仓库的 Python 工具依赖项、编译 Python 源目录以捕获语法错误，并运行 `pytest` 发现的所有测试，包括 `scripts/tests/` 和 `packages/character-system/engineering/generation/character-generator/tests/` 下的测试套件。

当 CI 失败时，请在仓库的 Actions 标签页中打开失败的运行，选择 `python-quality` 作业，展开失败的步骤以查看命令输出和回溯信息。
