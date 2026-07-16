# 工作流 Prompt：验证 Patch

在维护者修补后的任何兼容平台上使用。

```text
验证最近的 character-maintainer patch。

目标角色：
<绝对路径>

关联 patch note：
<路径或 id>

测试 prompt：
<prompt>

修补前行为：
<摘要或片段>

预期修补后行为：
<标准>

请：
1. 重新读取变更的文件及相邻文件。
2. 检查是否与 voice、style、anti-patterns、rubric 和 prompts 存在矛盾。
3. 运行任何可用的轻量级检查。
4. 编写 validation note 或验证摘要。
5. 声明 pass_or_fail。

除非验证揭示一个小而明显的修复且我批准，否则不要添加新的 patch 变更。
```
