# 工作流 Prompt：生成角色

在已暴露 `character-generator` 的平台上使用。

```text
使用 character-generator。

目标：
通过对话式 intake 生成一个与平台无关的新 character skill 包。不要要求我手写 JSON。

我可以提供的必要信息：
- Character id，如果已经决定：
- 显示名：
- 授权语料来源路径：
- 来源角色和类型：
- 授权确认：
- 隐私边界接受确认：
- 目标任务或交互类型：

我可以提供的可选信息：
- 输出目录：
- 语言：
- 隐私级别：
- 风格强度：
- 引用策略：
- 个人 profile / 背景取向：
- 期望关系姿态：
- 来源归一化偏好：
- 每个来源的 README 生成偏好：
- 发言人 / 上下文注释规则：
- 额外禁用任务或姿态：

更多要求：
- 我希望角色具备的强项：
- 它应该避免的表现：
- 成功输出示例：
- 敏感主题或边界：
- 其他约束：

请：
1. 先检查必要信息。
2. 如果必要信息不完整，停下来并报告缺失项。
3. 对缺失的可选信息使用安全默认值。
4. 运行对话式 intake 构建路径。
5. 报告验证、隐私、输出状态和 maintainer 后续需求。

不要：
- 提交语料文件。
- 使用未授权来源文本。
- 生成身份模仿 skill。
- 修改 maintainer 或运行时 character skill。
- 除非我要求，否则不要创建来源 README。
```

从 `workspace_manifest.yaml -> workspace.source_of_truth` 解析 `<workspace-root>`。
