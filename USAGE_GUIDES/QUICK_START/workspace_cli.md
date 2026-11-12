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

### DeepSeek 受控维护

先使用 `workspace skill dsh-preview --format json` 检查已批准的候选技能、
预期触发方式、来源和登记状态。该命令只读，不会加载技能、修改 Desktop 或授予
权限；`adaptation_required` 提示需审查平台适配，`adaptation_ready_for_verification`
表示已记录适配但仍需实际平台验收。`registration_required` 提示原技能未登记，
发现入口不等于具备注册技能的执行权限。
其中 authority 和 execution_modes 仅是登记信息，不代替逐项数据范围与副作用审查。

DSH 日常终端入口是 headless CLI；Desktop 保留相同的 Workspace TASK 与路径权限。
两个身份分别为 `deepseek-harness-cli` 和 `deepseek-harness`，由统一的
`workspace-kit` host guard 执行检查。CLI 启动器会从 Workspace 根目录启动，使用
`workspace-write` 沙箱，并额外开放 `.git` 元数据目录。文件工具访问 Workspace
之外的路径时，必须有当前活动 TASK，且逐路径 `workspace agent check` 通过该 TASK
范围和外部写入能力/Lease 检查；没有授权就拒绝。链接、凭据、私有语料、依赖和
`.git` 目录仍不能通过普通文件工具访问：

```powershell
scripts/platform/dsh-workspace-cli.cmd "按已解析的 Workspace TASK 执行工作"
```

在 DSH 会话中先调用 `workspace_task_start`，选择已登记的 TASK 类型；写入前解析
该 TASK 的必需上下文。`workspace_task_status` 查看当前 TASK，
`workspace_task_validate` 执行严格的变更范围和工作流检查，最后用
`workspace_task_finalize` 记录结果。守卫只接受当前 DSH session 自己拥有的活动 TASK；
其他会话的 TASK 默认只读。文件写入还会逐路径调用 `workspace agent check`。如需委派另一
TASK，负责人必须把准确 ID 写入 DSH `workspace-kit` 的 `delegatedTaskIds` 配置；这个本机
配置不在沙箱可写范围内。

Desktop 新会话默认使用 `workspace-write-quiet`。更改插件或 profile 后，完整退出并重启
DSH；已有会话保留旧权限选择。若守卫缺失、身份不匹配或 Workspace CLI 校验失败，写入和
Git 修改会被拒绝。禁止强推、重写历史、切换共享 worktree 分支以及写入未登记远端。
`origin/main` 集成必须通过合并预检、独立 Standards/Spec 代码审查和 audit-close；
无法提供独立审查凭据时停止在 main 集成之前。

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
