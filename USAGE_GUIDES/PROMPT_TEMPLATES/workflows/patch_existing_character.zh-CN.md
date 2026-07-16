# 工作流 Prompt：修补已有角色

在 `character-maintainer` 已曝光且 `source_patch` 模式已明确论证合理性的平台上使用。

```text
使用 character-maintainer。

目标角色文件夹：
<绝对路径>

诊断或 handoff：
<路径或粘贴的包文>

修补意图：
<应改进什么>

允许的文件：
<列表>

禁止触碰：
<列表>

请：
1. 验证诊断。
2. 记录 accepted/rejected/deferred。
3. 如果接受，修补最小的责任面。
4. 编写 patch note。
5. 验证变更后的行为。
6. 编写 validation note。
7. 建议是否需要 generalization note。

不要：
- 重写整个角色。
- 编辑 character-generator。
- 编辑无关的共享协议。
- 未经批准提交。
```
