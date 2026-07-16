# character-generator Prompt 模板

当前默认暴露平台：Codex。生成器的角色和权限与平台无关。

## 通过自然语言信息生成新角色

当你想创建一个基于个人语料或授权语料的 character skill，但不想手写
JSON 时，复制这一段使用。知道多少就填多少；可选项不知道可以留空。

```text
使用 character-generator。

我想从授权语料中创建一个风格启发型 character skill。请把下面的信息整理成安全的内部 intake / 构建计划。不要要求我手写 JSON。

必要信息：

1. 角色身份
- Character id，如果我已经决定：
- 希望用户看到的显示名 / 标签：

2. 授权语料来源
请为每个来源尽量提供：
- 路径：
- 来源类型：作品 / 聊天 / 笔记 / profile / 混合 / 未知
- 来源角色：长文风格、朋友聊天核心、批评声音、背景取向等
- 是否参与风格提取：是 / 否
- 是否在该来源目录生成或更新 README：是 / 否
- 如果是聊天类文本，发言人规则：
- 如果有上下文注释，处理规则：
- 其他说明：

3. 授权与隐私
- 我确认自己有权使用这些来源：是 / 否
- 我接受输出只能是风格启发，不是身份模仿：是 / 否
- 我接受不推断私人事实、不重构原文：是 / 否

4. 目标用途
- 主要任务：改写 / 续写 / 批评 / 风格迁移 / 讨论 / 朋友聊天 / 写作协作者 / 其他
- 典型使用场景：
- 期望语言：

可选信息：

- 首选输出目录，或者使用 character id 派生的默认目录：
- 隐私级别：高 / 中 / 低 / 使用安全默认值
- 风格强度：轻 / 中 / 强 / 使用安全默认值
- 引用策略或最大引用长度：
- 我提供的个人 profile 或背景取向：
- 期望关系姿态：朋友、批评者、写作伙伴、反思型陪伴者等
- 来源归一化偏好：保留错别字、清理标点、保留聊天节奏等
- 除身份模仿、私人事实推断、原文重构之外的禁用姿态或任务：
- 报告是否需要隐藏外部本地路径：
- 哪些来源只作为背景上下文，而不作为作者声音：

更多要求或偏好：

- 这个生成角色尤其应该擅长：
- 它应该避免听起来像：
- 我认为成功的输出示例：
- 需要额外谨慎的主题或边界：
- 其他我希望构建计划保留的东西：

任务：
1. 先检查必要信息是否完整。
2. 如果必要信息缺失，停下来并准确列出缺失项。
3. 如果只是可选信息缺失，使用安全默认值，并在最后报告质量缺口。
4. 使用对话式 intake 构建，不要求我手动编辑 JSON。
5. 只有在我要求时，才为来源生成或更新 README。
6. 启用 source planning 时，在生成的角色中生成 corpus reading handoff。

防护要求：
- 仅使用授权语料。
- 不要把私有语料放入 Git。
- 生成结果应是风格启发，而不是身份模仿。
- 不要从来源文本推断私人事实。
- 不要引用很长的私有原文。
- 不要修改 zyc 这类已经成熟演化的角色。
- 不要编辑 character-maintainer 或 style-doctor。

完成前：
- 在不暴露私有摘录的前提下，总结归一化后的构建计划。
- 总结生成的文件。
- 报告验证、隐私和可选信息警告。
- 告诉我是否建议后续由 maintainer 跟进。
- 除非我明确要求，否则不要提交。
```

## 通过配置生成新角色

当配置文件已经存在、需要可重复自动化构建时，使用这一段。

```text
使用 character-generator。

Character id：
<character_id>

显示名：
<display_name>

语料目录：
<workspace-root>\packages\character-system\engineering\generation\character-generator\corpus\<character_id>

配置文件：
<workspace-root>\packages\character-system\engineering\generation\character-generator\configs\<character_id>.json

任务：
读取已有配置，导入授权语料，并构建 character skill。

运行：
python scripts\build_character.py --config configs\<character_id>.json

预期输出：
<workspace-root>\packages\character-system\engineering\generation\character-generator\characters\<character_id>

防护要求：
- 仅使用授权语料。
- 不要把私有语料放入 Git。
- 生成结果应是风格启发，而不是身份模仿。
- 如果角色需要回应用户想法，而不只是转换文本，应包含有边界的聊天 / 讨论支持。
- 不要修改 zyc 这类已经成熟演化的角色。
- 不要编辑 character-maintainer 或 style-doctor。
- 如果配置缺失，停下来询问我是要提供对话式 intake，还是创建配置。

完成前：
- 总结生成的文件。
- 报告验证结果。
- 告诉我输出是否已经适合暴露给 OpenCode。
- 除非我明确要求，否则不要提交。
```

## 从语料更新已生成角色

```text
使用 character-generator。

目标配置：
<workspace-root>\packages\character-system\engineering\generation\character-generator\configs\<character_id>.json

更新后的语料：
<workspace-root>\packages\character-system\engineering\generation\character-generator\corpus\<character_id>

任务：
根据配置和语料重新构建这个已生成角色。

运行：
python scripts\build_character.py --config configs\<character_id>.json

防护要求：
- 这次重建可能会覆盖 characters\<character_id> 下的生成结果。
- 除非我明确批准，否则不要应用于手动演化过的角色。
- 不要从语料推断私人事实。
- 不要提交语料文件。

输出：
- 构建结果。
- 验证结果。
- 文件变更摘要。
- 任何隐私或生成警告。
```

从 `workspace_manifest.yaml -> workspace.source_of_truth` 解析 `<workspace-root>`。
