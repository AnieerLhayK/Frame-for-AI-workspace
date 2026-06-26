# Workspace CLI 小白使用指南

## 它是什么

`workspace_cli.py` 是这个 workspace 的统一维护入口。

你可以把它理解成一个本地控制台：

- 告诉你某类任务应该读哪些文件；
- 帮你找到工程现状、skill 开发经验和管理规则；
- 当多个文件都可能修改时，比较哪一组更合理；
- 检查报告是否过期；
- 检查 workspace、协议和 skill 加载链接。

它不会代替维护 agent 编写和修改代码。它负责在动手前缩小范围、在动手后帮助验证，减少无关文件读取、错误修改和重复分析。

当前 CLI 全部在本机运行，不会调用 LLM，也不会消耗 OpenAI、Claude 或其他模型额度。`tiktoken` 只在本机计算文本 token 数量。

## 从哪里运行

最简单的方式是在 PowerShell 进入 workspace：

```powershell
$workspaceRoot = "<workspace-root>"
Set-Location $workspaceRoot
```

然后运行：

```powershell
python scripts\workspace_cli.py --help
```

如果你不在 workspace 目录，也可以使用完整路径：

```powershell
python "$workspaceRoot\scripts\workspace_cli.py" --help
```

## 安装短命令

只需运行一次：

```powershell
python scripts\workspace_cli.py launcher install
```

之后可以直接输入：

```powershell
workspace health
workspace task list
workspace knowledge find "工程现状"
```

检查安装状态：

```powershell
workspace launcher status
```

卸载：

```powershell
workspace launcher uninstall
```

默认只在当前用户的 `.local\bin` 下管理 `workspace.cmd`，不修改
PowerShell profile 或系统 PATH。如果目标位置已有非本工具生成的同名命令，
安装和卸载都会停止，不覆盖也不删除。

## 第一次使用

先试这四条：

```powershell
python scripts\workspace_cli.py task list
python scripts\workspace_cli.py knowledge find "工程现状"
python scripts\workspace_cli.py reports status
python scripts\workspace_cli.py validate links
```

它们分别用于：

1. 查看 workspace 认识哪些任务；
2. 找到当前工程状态应该阅读的文件；
3. 查看当前报告是否过期；
4. 检查 Codex 和 OpenCode 的 skill 链接是否正常。

这四条都是只读操作。

如果只想用一条命令完成这些基础检查：

```powershell
python scripts\workspace_cli.py health
```

加上完整脚本测试：

```powershell
python scripts\workspace_cli.py health --with-tests
```

查看当前 workspace 版本、Git 状态、能力数量和最近治理记录：

```powershell
workspace summary
workspace summary --format json
```

这个命令只读取 manifest、Git、registry 和最近的 ledger 条目，不会生成报告或修改文件。

## 推荐的日常流程

### 1. 先确定任务类型

```powershell
python scripts\workspace_cli.py task list
```

例如你想修改 skill 的发现 metadata，可以看到任务 id：

```text
skill_metadata_update
```

### 2. 解析任务

```powershell
python scripts\workspace_cli.py task resolve skill_metadata_update `
  --bind target-skill=packages/character-system/engineering/generation/character-generator
```

输出会告诉你：

- 必须读取哪些文件；
- 哪些文件是可选的；
- 哪些目录默认忽略；
- 允许修改哪些文件；
- 完成后运行哪些验证。

`--bind` 用来填写任务里的占位符。不要让维护 agent 通过扫描整个目录来猜占位符。

### 3. 检查上下文预算

```powershell
python scripts\workspace_cli.py preflight skill_metadata_update `
  --bind target-skill=packages/character-system/engineering/generation/character-generator
```

如果所需上下文太大，严格检查会返回非零退出码。你可以先缩小任务，而不是一开始就读取大量文件。

如果命令提示缺少文件或占位符，但你看不懂原因：

```powershell
python scripts\workspace_cli.py failure check skill_metadata_update
```

它会把结果分为：

- `READY`：必要资源完整；
- `DEGRADED`：缺少可选资源，可以在明确限制后继续；
- `BLOCKED`：缺少必要资源、路径越界或占位符未填写，必须停止。

检查可选资源：

```powershell
python scripts\workspace_cli.py failure check skill_metadata_update `
  --bind target-skill=packages/character-system/engineering/generation/character-generator `
  --include-optional
```

### 4. 找不到知识入口时再搜索

```powershell
python scripts\workspace_cli.py knowledge find "skill 开发"
python scripts\workspace_cli.py knowledge find "错误处理"
python scripts\workspace_cli.py knowledge find "报告刷新"
```

它只搜索知识注册表，不会遍历整个 workspace。返回结果中的文件才是建议阅读入口。

### 5. 多种修改方案难以选择时再规划

自动分析任务的可写层：

```powershell
python scripts\workspace_cli.py changes plan developer_interface_tooling `
  --intent tooling
```

比较两套具体方案：

```powershell
python scripts\workspace_cli.py changes plan developer_interface_tooling `
  --intent tooling `
  --option "implementation=scripts/workspace_cli.py,scripts/tests/test_workspace_cli.py" `
  --option "docs-only=README.md"
```

After editing, compare actual Git changes with the same task id:

```powershell
workspace changes verify change_scope_verification
workspace changes verify skill_metadata_update `
  --bind target-skill=skills/example-skill
```

The verifier reads unstaged, staged, and untracked paths by default and does
not write reports or modify Git:

```powershell
workspace changes verify <task-id> --format json
workspace changes verify <task-id> --strict
workspace changes verify <task-id> --no-include-staged
workspace changes verify <task-id> --no-include-untracked
```

- `PASS`: every actual path is declared by the resolved task.
- `WARNING`: part of the scope is descriptive and needs human review.
- `ERROR`: a path is out of scope, a high-risk path is undeclared, or
  task/Git resolution failed.

On ERROR, keep every file and stop expanding the change set. Choose a better
task id, transfer work to another task or safety branch, manually select legal
changes, or use a worktree for destructive/high-risk work. The verifier never
runs reset, checkout, clean, delete, stage, commit, or rollback commands.

For normal daily maintenance, run one read-only summary after editing:

```powershell
workspace workflow check <task-id>
```

It resolves the task, runs the same scope verifier, checks both unstaged and
staged diffs with `git diff --check`, and prints the task's validation commands.
It does not execute those tests or perform any Git write. The practical flow is:

```text
resolve -> plan only if needed -> edit -> verify -> validate -> inspect diff -> commit
```

Use `changes verify` when you need the detailed path evidence by itself. Use
`workflow check` when deciding whether the current task is ready for its routed
validation and commit review.

For work produced by a non-default maintainer, include the actor and active
Skill:

```powershell
workspace changes verify <task-id> --agent hermes --skill style-doctor
workspace workflow check <task-id> --agent hermes --skill style-doctor
```

Task scope, Agent authority, and Skill execution mode must all allow the
change. A broad task route cannot override a denied Agent or Skill boundary.

可能看到：

- `VIABLE`：包含真正负责该行为的文件层；
- `SUPPORTING_ONLY`：只能作为配套修改；
- `BLOCKED`：越权、使用 projection 路径，或修改了错误层。

规划结果只是调查起点，不代表必须修改列出的所有文件。

### 6. 修改完成后检查

```powershell
python scripts\workspace_cli.py reports status --strict
python scripts\workspace_cli.py validate links
```

再运行任务解析结果中列出的测试或验证命令。

## 当前命令总览

| 命令 | 用途 | 是否写文件 |
| --- | --- | --- |
| `task list` | 查看任务 id | 否 |
| `task resolve` | 获取最小上下文、写入范围和验证命令 | 否 |
| `prompt list` | 查看 prompt id | 否 |
| `prompt show` | 解析一个 prompt | 否 |
| `preflight` | 严格检查任务资源和 token 预算 | 否 |
| `bootstrap` | 确认 workspace 根目录和 manifest | 否 |
| `health` | 汇总 workspace、知识索引、报告和链接状态 | 否 |
| `summary` | 查看实时版本、Git、能力清单和最近治理记录 | 否 |
| `skill init` | 创建尚未注册的新 skill 源码骨架 | 是，仅指定的 workspace 源码路径 |
| `skill validate` | 检查 metadata、基础文件和 manifest 必需文件 | 否 |
| `skill list` | 查看已注册 skill、源码和 projection 状态 | 否 |
| `skill expose` | 预览或建立单个 manifest projection | 默认否；`--apply` 会写平台目录 |
| `launcher install/status/uninstall` | 管理 `workspace` 短命令 | install/uninstall 会修改用户 bin |
| `failure check` | 解释任务缺少什么以及能否继续 | 否 |
| `knowledge list/find/validate` | 查找并验证知识入口 | 否 |
| `changes plan` | 比较候选修改面 | 否 |
| `reports status` | 检查报告是否过期 | 否 |
| `reports refresh` | 重新生成指定报告 | 是 |
| `validate links` | 检查 platform projection | 否 |
| `validate manifest` | 验证 manifest 并刷新报告 | 是，仅报告 |
| `validate protocols` | 验证 shared 协议并刷新报告 | 是，仅报告 |

## 新 Skill 生命周期

先创建一个尚未登记的源码骨架：

```powershell
python scripts\workspace_cli.py skill init example-skill `
  --source-path skills/example-skill `
  --description "Use when handling example tasks."
```

该命令会创建 `SKILL.md`、`README.md`，以及按需使用的
`references/`、`scripts/`、`tests/`、`assets/` 入口说明。它不会擅自修改
`workspace_manifest.yaml`，也不会建立平台链接。

完善 skill 内容后，在 manifest 中登记其角色、权限、执行模式、必需文件和
projection。然后验证：

```powershell
python scripts\workspace_cli.py skill validate example-skill
```

也可以直接验证 manifest 中登记的源码路径：

```powershell
python scripts\workspace_cli.py skill validate skills/example-skill
```

查看当前所有 skill：

```powershell
python scripts\workspace_cli.py skill list
python scripts\workspace_cli.py skill list --platform codex --format json
```

平台暴露默认只预览：

```powershell
python scripts\workspace_cli.py skill expose example-skill --platform codex
```

确认输出中的 source 和 link path 后，才显式执行：

```powershell
python scripts\workspace_cli.py skill expose example-skill --platform codex --apply
```

`skill expose` 只使用 manifest 已登记的 projection。遇到现有真实目录、
错误链接或失效 junction 时会返回 `BLOCKED` 并保留原物，不会自动删除或替换。

## Prompt 库怎么用

查看 prompt：

```powershell
python scripts\workspace_cli.py prompt list
python scripts\workspace_cli.py prompt show minimal_edit
```

需要完整模板内容时：

```powershell
python scripts\workspace_cli.py prompt show zyc_natural_discussion `
  --include-template
```

Prompt 注册表主要减少重复编写复杂元提示词。它不会自动把 prompt 发送给任何模型。

## 报告命令要特别注意

只查看，不修改：

```powershell
python scripts\workspace_cli.py reports status
```

明确刷新，报告文件会变化：

```powershell
python scripts\workspace_cli.py reports refresh manifest-validation
python scripts\workspace_cli.py reports refresh protocol-validation
python scripts\workspace_cli.py reports refresh workspace
```

批量刷新当前报告：

```powershell
python scripts\workspace_cli.py reports refresh all-current
```

不要为了让报告看起来正确而手工修改报告结论。应修改事实来源，再运行对应生成器。

## 如何查看帮助

查看总帮助：

```powershell
python scripts\workspace_cli.py --help
```

查看某一组命令：

```powershell
python scripts\workspace_cli.py task --help
python scripts\workspace_cli.py knowledge --help
python scripts\workspace_cli.py changes --help
python scripts\workspace_cli.py reports --help
```

继续查看具体命令：

```powershell
python scripts\workspace_cli.py task resolve --help
python scripts\workspace_cli.py knowledge find --help
python scripts\workspace_cli.py reports refresh --help
```

## 文本输出和 JSON 输出

平时阅读使用默认文本输出即可。

当你希望把结果交给脚本、agent 或其他工具处理时：

```powershell
python scripts\workspace_cli.py knowledge find "工程现状" --format json
```

通常的退出码：

- `0`：成功或检查通过；
- `1`：参数、资源或执行错误；
- `2`：严格检查发现预算、过期状态或需要人工复核的问题。

## 当前能力和后续规划

当前已经完成十三组能力：

1. task 路由；
2. prompt 路由；
3. preflight 上下文预算；
4. workspace bootstrap；
5. validation；
6. report freshness 与刷新；
7. change-surface 方案比较；
8. knowledge 主题检索。
9. live workspace health 汇总。
10. required/optional 故障诊断。
11. 用户级 `workspace` 短命令。
12. 实时版本与治理摘要。
13. skill 初始化、验证、清单和受控平台暴露。

当前规划的单 agent 开发者 CLI 路线已经完成。下一阶段应先进入实际使用和观察期，
根据真实重复操作再决定是否增加命令。多 agent 调度属于未来独立的架构阶段，
不应直接塞进现有 CLI。

## 最短记忆版

只需要记住：

```text
不知道任务类型：task list
知道任务类型：task resolve
不知道读什么：knowledge find
不知道改哪里：changes plan
不知道报告是否可信：reports status
不知道 skill 链接是否正常：validate links
想创建或检查 skill：skill init / validate / list
想建立单个 skill 链接：skill expose（先预览，再 --apply）
想一次检查基础设施：health
看不懂资源错误：failure check
```
