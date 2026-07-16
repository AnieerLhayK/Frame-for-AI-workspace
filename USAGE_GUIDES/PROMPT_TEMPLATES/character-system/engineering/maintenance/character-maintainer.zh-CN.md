# character-maintainer Prompt 模板

当前默认曝光：Codex。源码修补仍需维护者权限和 `source_patch` 模式。

## 从诊断快速修补

```text
使用 character-maintainer。

目标角色：
<角色文件夹路径>

诊断或 handoff：
<路径、id 或粘贴的包文>

任务：
审查诊断，检查当前源文件，在编辑前决定 accepted / rejected / deferred。

防护措施：
- 将 style-doctor 生成的任何源 diff 仅视为候选修补材料。
- 不要假设 doctor 的变更已获批准。
- 不要修改 character-generator。
- 如果接受，仅修补最小的责任面。
- 仅在维护者决定后写入/更新 runtime-loop 记录。
- 除非我明确要求，否则不要提交。
```

## 从反馈修补已有角色

```text
使用 character-maintainer。

目标角色：
<角色文件夹的绝对路径>

反馈：
"<用户反馈或观察到的失败>"

允许修补范围：
<可以更改的文件或文件夹>

禁止触碰：
<不得更改的文件、文件夹或行为>

验证预期：
<测试 prompt、前后行为对比或验收标准>

任务：
先诊断，然后仅修补最小的责任面。

防护措施：
- 不要编辑 character-generator。
- 不要编辑生成器模板。
- 不要重写整个角色。
- 保留手动演化和示例，除非它们直接导致失败。
- 如果经验可能泛化，编写 generalization note 而非更改生成器资产。
- 显示 git diff 摘要并在提交前等待批准。

必需输出：
- 诊断摘要。
- 维护者决定：accepted、rejected 或 deferred。
- 变更的文件。
- Patch note。
- Validation note 或验证摘要。
- 泛化建议（如有）。
```

## 从 style-doctor 诊断结果修补

```text
使用 character-maintainer。

目标角色：
<角色文件夹的绝对路径>

诊断来源：
<诊断包文路径、handoff 包文路径或粘贴的诊断摘要>

任务：
审查诊断，决定 accepted/rejected/deferred，仅在接受时应用窄修补。

防护措施：
- 在此轮中不要修改 character-generator。
- 没有 generalization note 时不要从一个角色泛化。
- 不要更改无关文件。
- 保留现有手动优化。

Runtime-loop 记录：
- 编写或更新 patch note。
- 编写或更新 validation note。
- 如果是正式的 runtime-loop 案例，更新 patch ledger。
- 仅当经验合理地可复用时创建 generalization note。

最终响应：
- 决定。
- 修补摘要。
- 验证结果。
- 剩余风险。
- 是否需要单独开启生成器任务。
```
