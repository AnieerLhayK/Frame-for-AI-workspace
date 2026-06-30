# Prompt 模板

这是打开 `USAGE_GUIDES/` 的主要原因。

选择最接近你任务的模板，填入路径和反馈，然后在技能的 manifest exposure 中声明的平台上运行。

对于工作区维护 prompt，在打开完整模板之前，先通过 `USAGE_GUIDES/prompt_registry.yaml` 解析 prompt id。这样可以避免每次会话重复生成相同的元 prompt。

本层与 `../REFERENCE/` 有意区分：模板是可直接复制使用的操作性文本，而参考页面则解释角色和选择边界。不要在此处镜像完整的参考内容；当需要背景说明时，链接到参考材料即可。

## 当前曝光模板

- `packages/character-system/engineering/generation/character-generator.md`
- `packages/character-system/engineering/maintenance/character-maintainer.md`
- `packages/character-system/runtime/zyc.md`
- `packages/character-system/engineering/diagnosis/style-doctor.md`

## 工作流模板

- `workflows/generate_character.md`
- `workflows/diagnose_runtime_drift.md`
- `workflows/patch_existing_character.md`
- `workflows/validate_patch.md`
- `workflows/generator_generalization.md`

## 工作区维护模板

- `workspace-maintenance/prompt-library-maintenance.md`
- `workspace-maintenance/workspace-health-remediation.md`
- `workspace-maintenance/scoped-change-planning.md`
- `workspace-maintenance/task-handoff-continuation.md`
- `workspace-maintenance/branch-merge-review.md`

## 模板规则

将防护措施保留在复制后的 prompt 内部。它们可以防止意外的大范围重写、生成器污染以及源/投影混淆。

模板路径遵循领域和生命周期角色。平台兼容性通过 manifest exposure 声明，而非模板目录名称。

如果模板和参考页面开始出现偏差，应将模板视为可执行防护措施的载体，将参考页面视为简洁说明的载体。
