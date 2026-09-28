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

## 日常读取

```powershell
workspace task list
workspace task resolve <task-id>
workspace preflight <task-id>
workspace knowledge find "skill 开发"
workspace explain path scripts/workspace/workspace_cli.py
```

`task resolve` 给出 required/optional context、write scope 和验证命令；需要占位值时传入 `--bind name=value`。`preflight` 还会检查必需上下文的 token 预算。知识搜索只查登记的知识入口，不扫描全仓库。

## 写入前检查权限

先登记任务，再检查目标路径是否获准：

```powershell
workspace records start --task-type <task-id> --operation workspace_write `
  --owner-agent codex --owner-session <session-id>
workspace agent check --agent codex --path <workspace-relative-path>
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

## 常用只读检查

```powershell
workspace health
workspace reports status
workspace validate links
workspace skill list
```

刷新报告或建立平台投影会写文件。先查看对应命令帮助，并仅在任务明确授权时使用写入选项。

## 帮助

```powershell
workspace <command> --help
workspace <command> <subcommand> --help
```
