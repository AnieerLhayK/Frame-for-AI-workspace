# 使用指南

`USAGE_GUIDES/` 是该工作区的提示词优先使用层。

当你需要运行一个技能、复制一份安全的提示词模板、了解某个技能当前在哪个平台暴露、或遵循跨平台工作流时，请使用此文件夹。

## 从这里开始

1. 打开 `START_HERE.md`。
2. 在维护或开发工作区时，打开 `QUICK_START/workspace_cli.md`。
3. 需要提示词库入口点时，打开 `PROMPT_LIBRARY.md`。
4. 需要可复用的提示词 ID 或任务特定提示词框架时，查看 `prompt_registry.yaml`。
5. 从 `PROMPT_TEMPLATES/` 复制一份提示词。
6. 如果不确定使用哪个平台，查看 `QUICK_START/`。
7. 需要详细的角色或工作流指导时，打开 `REFERENCE/README.md`。

## 这是什么

- 一个低维护的用户指南层。
- 一个提示词模板库。
- 一个用于可复用提示词 ID 和元提示词的提示词注册表。
- 一个按运行时和工程角色组织的实用使用地图，在部署细节不同的地方附带单独的平台加载指导。
- 一个存放安全调用模式的地方。

## 这不是什么

- 不是真相来源。真相依然在 `workspace_manifest.yaml`。
- 不是协议层。协议位于 `shared/`。
- 不是当前项目记忆。项目记忆位于 `PROJECT_CONTEXT/`。
- 不是运行时漂移记录。运行时漂移记录位于 `packages/character-system/reports/runtime-loop/`。

## 主要入口点

- `PROMPT_TEMPLATES/`：可直接复制的提示词。
- `PROMPT_LIBRARY.md`：提示词库的目的、命令、成熟度和构建计划。
- `prompt_registry.yaml`：用于任务路由、可复用元提示词和模板查找的提示词 ID 注册表。
- `QUICK_START/`：简短平台使用说明。
- `QUICK_START/workspace_cli.md`：统一维护 CLI 的初学者指南。
- `REFERENCE/README.md`：按角色和工作流分类的详细指导索引。
- `REFERENCE/runtime/`：面向用户的运行时技能详情。
- `REFERENCE/engineering/`：生成、诊断、维护和生命周期详情。
- `REFERENCE/workflows/`：跨越多个角色的端到端工作流。
- `REFERENCE/platforms/`：特定于平台的加载和安全说明。
- `SAFETY.md`：避免常见误用的简洁护栏。

## 参考与模板的区分

`REFERENCE/` 和 `PROMPT_TEMPLATES/` 可能涉及同一个技能或工作流，但它们并非重复的来源：

- 使用 `REFERENCE/` 获取解释、角色边界和何时使用的指导。
- 使用 `PROMPT_TEMPLATES/` 获取可以复制到 AI 会话中的文本。

当两个层都需要相同的安全规则时，将完整的操作措辞保留在提示词模板中，并让参考指南指向该模板，而不是重复冗长的提示词文本。
