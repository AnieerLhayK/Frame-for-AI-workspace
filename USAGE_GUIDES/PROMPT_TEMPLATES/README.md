# Prompt Templates

This is the main reason to open `USAGE_GUIDES/`.

Copy the template closest to your task, fill in paths and feedback, then run it on a platform listed in the skill's manifest exposure.

For workspace maintenance prompts, resolve the prompt id through `USAGE_GUIDES/prompt_registry.yaml` before opening full templates. This avoids regenerating the same meta-prompt each session.

This layer is intentionally different from `../REFERENCE/`: templates are
copy-ready operational text, while reference pages explain roles and selection
boundaries. Do not mirror full reference prose here; link to reference material
when background explanation is needed.

## Current Exposure Templates

- `packages/character-system/engineering/generation/character-generator.md`
- `packages/character-system/engineering/maintenance/character-maintainer.md`
- `packages/character-system/runtime/zyc.md`
- `packages/character-system/engineering/diagnosis/style-doctor.md`

## Workflow Templates

- `workflows/generate_character.md`
- `workflows/diagnose_runtime_drift.md`
- `workflows/patch_existing_character.md`
- `workflows/validate_patch.md`
- `workflows/generator_generalization.md`

## Workspace Maintenance Templates

- `workspace-maintenance/prompt-library-maintenance.md`
- `workspace-maintenance/workspace-health-remediation.md`
- `workspace-maintenance/scoped-change-planning.md`
- `workspace-maintenance/task-handoff-continuation.md`
- `workspace-maintenance/branch-merge-review.md`

## Template Rule

Keep guardrails inside the copied prompt. They prevent accidental broad rewrites, generator contamination, and source/projection confusion.

Template paths follow domain and lifecycle role. Platform compatibility is
declared through manifest exposures, not template directory names.

If a template and a reference page start drifting, treat the template as the
place for executable guardrails and the reference page as the place for concise
explanation.
