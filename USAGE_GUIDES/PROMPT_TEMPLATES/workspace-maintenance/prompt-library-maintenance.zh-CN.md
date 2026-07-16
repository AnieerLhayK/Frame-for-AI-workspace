# Prompt 库维护

在扩展工作区 prompt 库本身时使用此 prompt。

## 基础任务

```text
任务：
改善工作区 prompt 库，但不更改任务权限、工作区治理、模型设置或平台配置。

从此处开始：
- `USAGE_GUIDES/PROMPT_LIBRARY.md`
- `USAGE_GUIDES/prompt_registry.yaml`
- `USAGE_GUIDES/PROMPT_TEMPLATES/README.md`
- `PROJECT_CONTEXT/todo/README.md`
- `PROJECT_CONTEXT/task_ledger/README.md` 中的最新条目

目标：
添加或优化 prompt id 和可复制模板，使常见的 AI 维护工作能够复用稳定的指令，而非每次重新生成长 prompt。

防护措施：
- 保持 prompt id 小而稳定。
- 对于简短的路由指导，优先使用 `prompt_frame`。
- 对于可复制 prompt 或多锚点变体，优先使用模板文件。
- 不要在 prompt 文本中重复任务注册表的权限。
- 不要暗示 prompt 授予写权限、工具访问权限、模型访问权限或绕过 Git 检查的权限。
- 验证注册的模板路径存在。
- 除非明确要求，否则不要提交。
```

## 验收检查

更改 prompt 库文件后运行针对性的检查：

```powershell
workspace prompt list
workspace prompt show prompt_library_maintenance --include-template
python scripts/resolve_task_context.py --prompt-id prompt_library_maintenance --include-template
git diff --check
```

如果任务路由或验证行为发生变化，在编辑脚本之前使用匹配的工作区任务路由。
