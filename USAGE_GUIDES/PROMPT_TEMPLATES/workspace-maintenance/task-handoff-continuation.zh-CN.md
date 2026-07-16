# 任务 Handoff 延续

在继续之前的工作区维护线程或根据 handoff 说明工作时使用此 prompt。

```text
任务：
根据提供的 handoff 继续此工作区维护工作：
<粘贴 handoff 或路径>

开始：
1. 运行 `git status --short --branch --untracked-files=all`。
2. 运行 `git log -5 --oneline --decorate`。
3. 仅读取 handoff、最新的 task ledger 条目和已解析的任务上下文。
4. 在编辑前解析当前任务 id。

防护措施：
- 不要假设 handoff 是最新的；将其与 Git 状态进行比较。
- 不要重放已经合并或已被取代的旧操作。
- 除非已解析的任务需要，否则不要读取广泛的报告或归档。
- 保留用户变更。
- 除非明确要求，否则不要提交或推送。

预期输出：
- 当前分支及其干净程度。
- Handoff 说明已完成的内容。
- Git 实际已完成的内容。
- 下一个安全操作。
- WORKSPACE_ENGINEERING writeback 是否适用。
```
