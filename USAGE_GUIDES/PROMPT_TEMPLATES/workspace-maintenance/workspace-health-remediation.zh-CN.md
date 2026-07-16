# 工作区健康修复

当 `workspace health` 报告 NEEDS_ATTENTION 或 FAIL，且下一步应基于源码诊断而非猜测时使用此 prompt。

```text
任务：
诊断并修复当前的 `workspace health` 输出。

开始：
1. 运行 `workspace health`。
2. 如果报告已过时，在更改源码前运行 `workspace reports status --strict`。
3. 使用 `workspace task list` 或 `python scripts/resolve_task_context.py --list` 选择最小的匹配任务 id。
4. 在编辑前解析该任务。

防护措施：
- 不要手动编辑生成的报告结论。
- 在源码变更或过期报告证据证明合理之前，不要刷新报告。
- 不要将跳过的测试视为失败；解释它们为何被跳过。
- 保持 health 文本渲染、源码行为和报告快照分离。
- 除非已解析的任务明确拥有该表面，否则不要更改外部工具、模型设置、提供者凭据或平台配置。
- 保留现有用户变更，除非明确要求否则不要提交。

预期输出：
- 说明哪些 health 组正在失败或已过时。
- 指出拥有该失败的源文件或报告生成器。
- 提出最小的修复路径和验证命令。
- 说明 WORKSPACE_ENGINEERING writeback 是否适用。
```
