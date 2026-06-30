# 代理变更请求

本目录是供不具备修改请求工作空间表层所需能力的代理使用的审查收件箱。

请求是治理记录，而非生成的报告快照，也非授权。Codex、Claude Code 或用户必须在结构性工作开始之前审查每个请求。

使用以下命令生成请求：

```powershell
workspace agent request --agent hermes --mode worktree `
  --summary "注册缺失的技能暴露" `
  --path workspace_manifest.yaml
```

请勿将租约文件放置于此。临时租约属于外部运行时状态。
