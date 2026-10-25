# Workspace CLI 入门

`workspace` 是本地维护控制台：解析任务所需上下文和写入范围，查找知识入口，并运行只读状态与验证检查。它不调用模型。

## 启动

在工作区根目录运行：

```powershell
workspace --help
```

尚未安装短命令时，可用 `python -m scripts.workspace.workspace_cli` 代替 `workspace`。查看或管理短命令：

```powershell
workspace launcher status
python -m scripts.workspace.workspace_cli launcher install
```

向 PLAN 等命令传递多行正文时，用 Python 子进程参数列表调用模块入口，避免 `.cmd`
对复杂参数进行二次解析；保存后核对记录正文和验收条件。

## 日常读取

```powershell
workspace task list
workspace task resolve <task-id>
workspace preflight <task-id>
workspace knowledge list
workspace knowledge validate
workspace explain path scripts/workspace/workspace_cli.py
```

`task resolve` 给出 required/optional context、write scope 和验证命令；需要占位值时传入 `--bind name=value`。`preflight` 还会检查必需上下文的 token 预算。知识搜索只查登记的知识入口，不扫描全仓库。

## 写入前检查权限

先登记任务，再检查目标路径是否获准：

```powershell
workspace records start --task-type <task-id> --operation workspace_write `
  --owner-agent codex --owner-session <session-id>
workspace agent check --agent codex --path <workspace-relative-path> --record-id <TASK-ID>
```

如果权限不足，可提交审查或临时授权申请；申请本身不会授予权限：

```powershell
workspace agent request --agent codex --mode review_only `
  --summary "<change>" --path <workspace-relative-path>
workspace agent lease validate <lease-file>
```

执行期间保持 TASK 有效。完成后运行登记的验证和：

```powershell
workspace workflow check <task-id> --record-id <TASK-ID>
```

`workflow check` 检查写入范围、Git diff 和工作流就绪状态；它不会代替任务的验证命令，也不会提交。Agent 权限、skill 权限/执行模式和 TASK 写入范围必须同时允许操作。

同一状态、同一范围内，`workflow check` 已包含 `changes verify` 与未暂存/已暂存的
diff 检查，无需再分别重复运行。整批交付加 `--include-committed`；文件、暂存区或
提交变化后重新检查。检查其他范围、排查失败和独立测试仍按需要执行。
登记验证命令若使用 `$env:WORKSPACE_TASK_RECORD`，先把它设为本轮的准确活动 TASK；
批量协作仍显式传入 `--batch-task` 和经协调的路径，不能借此扩大写入权限。

## 常用只读检查

```powershell
workspace health
workspace reports status
workspace validate links
workspace skill list
```

只验证 manifest 或 protocol、不刷新报告时使用：

```powershell
workspace validate manifest --check
workspace validate protocols --check
```

两个验证器的模块入口也支持 `--check`；验证失败仍返回非零。`--help` 不验证或写报告。
为兼容既有调用，不带 `--check` 的验证仍会写报告；显式刷新使用
`workspace reports refresh <report-id>`。触碰或恢复旧报告不会清除 Git 已知的陈旧证据。
协议验证属于 Workspace 私有能力；公开 Frame 模板仅附带 manifest 验证器，模板项目
需先接入自己的协议验证器，再使用这里的 protocol 命令。

刷新报告或建立平台投影会写文件。先查看对应命令帮助，并仅在任务明确授权时使用写入选项。

## 帮助

```powershell
workspace <command> --help
workspace <command> <subcommand> --help
```
