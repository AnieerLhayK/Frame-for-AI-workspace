# 任务结果记录

此受 Git 跟踪的目录保存每项工作区任务的机器可读事实。每项任务一个 JSON 文件，路径为 `YYYY/MM/DD/TASK-*.json`；字段定义和兼容性规则见 `schema.json`。

## 写入前必须登记

任何工作区源文件写入，或由工作区发起的外部写入，都必须先建立一条活动记录；纯只读调查不受此要求约束。

```powershell
$record = (workspace records start --task-type <route> --operation workspace_write --tokens-estimated <count> | ConvertFrom-Json).task_id
$env:WORKSPACE_TASK_RECORD = $record  # Claude/OpenCode 写入适配器需要此变量

# 同一任务还会修改已批准的外部目标时，在登记时同时声明：
workspace records start --task-type <route> --operation workspace_write --operation external_write
```

`start` 会分配当天唯一的任务 ID。`init` 仅供已经由集成层分配了 ID 的场景使用；不要用它修改已经存在的记录。

写入闸门使用同一 ID：

```powershell
workspace records require $record --operation workspace_write
workspace agent check --agent codex --path scripts/example.py --record-id $record
workspace workflow check <route> --record-id $record
```

外部目标还必须在记录中声明 `external_write`；`workspace agent check` 会根据目标路径自动选择该范围。在记录仍为 `in_progress` 时运行 `workflow check`，验证完成后再结束记录：

```powershell
workspace records finalize $record --status successful --validation passed --usability usable --human-edit-rounds 1
```

所有记录都应提交到 Git：它们是可审查、可长期追溯的任务事实。不要存放服务商完整转录、密钥、原始提示词或易变工具日志。图表和周期性报告应放在 `reports/`，并能由这些记录再生成。

维护重点是 schema 兼容性、证据质量、指标定义稳定性和按日分区。新的可选字段应加入具名对象；改变既有字段含义时必须升级 schema 版本并提供迁移。不得把按日记录重新汇总为月度文件。
