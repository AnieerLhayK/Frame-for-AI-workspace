# Agent Ecosystem Workspace

本工作区由 `workspace_manifest.yaml` 统一管理：技能源目录、角色、权限、执行模式、共享协议及平台暴露均以该文件为事实来源。

## 项目上下文

新会话应先阅读 `ARCHITECTURE.md`，再阅读 `PROJECT_CONTEXT/README.md`、`current_status.md` 与 `todo.md`。`PROJECT_CONTEXT/` 保存当前任务记忆、台账、注册表、状态和待办，但不替代 manifest、架构说明、`shared/` 协议、报告或运行时记录。

这是受治理的技能单体仓库，而非巨型 Agent。新增技能前，请判断它应位于既有领域包、新领域包、独立技能目录，还是独立工作区；不要把无关业务规则堆入顶层 `shared/`。平台加载面不代表能力所有权。

## Claude Code 项目边界

Claude Code 以启动目录作为项目根。本工作区通过根目录 `CLAUDE.md` 和受跟踪的 `.claude/` 规则注册为受治理的技能工作区。

```powershell
claude-workspace
claude-cnn
claude-ztemp
claude-project <alias>
```

也可在目标 Git 根目录执行 `claude`。请勿在已运行会话中切换仓库；应从目标项目重新启动，以加载正确的守卫规则。

## 工程知识与维护流程

`WORKSPACE_ENGINEERING/` 是可复用的 AI 工作区工程知识库；`USAGE_GUIDES/` 提供可直接复制的提示词、技能参考和平台加载说明。

1. 运行 `git status --short`。
2. 必要时运行 `python scripts/resolve_task_context.py --list` 查找任务 ID。
3. 运行 `python scripts/resolve_task_context.py <task-id>`，仅读取必需上下文。
4. 修改最窄责任层并执行相应验证。
5. 长期决策、风险或后续步骤变化时更新 `PROJECT_CONTEXT/`。

## 常用命令

```powershell
python scripts\workspace_cli.py task list
python scripts\workspace_cli.py task resolve platform_exposure
python scripts\workspace_cli.py health
python scripts\workspace_cli.py summary
python scripts\workspace_cli.py agent status
python scripts\workspace_cli.py skill list
python scripts\workspace_cli.py validate links
```

解析器结合任务注册表、提示词注册表与上下文预算。使用 `--format json` 可供脚本或 Agent 集成；安装 `scripts/requirements-context-tools.txt` 后可得到精确的 `o200k_base` Token 估算。

## 验证与持续集成

```powershell
python scripts\validate_manifest.py
python scripts\validate_protocols.py
powershell -ExecutionPolicy Bypass -File scripts\check_links.ps1
python scripts\workspace_cli.py health --with-tests
```
