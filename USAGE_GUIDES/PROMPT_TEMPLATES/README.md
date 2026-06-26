# Prompt Templates

This is the main reason to open `USAGE_GUIDES/`.

Copy the template closest to your task, fill in paths and feedback, then run it on a platform listed in the skill's manifest exposure.

For workspace maintenance prompts, resolve the prompt id through `USAGE_GUIDES/prompt_registry.yaml` before opening full templates. This avoids regenerating the same meta-prompt each session.

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

## Template Rule

Keep guardrails inside the copied prompt. They prevent accidental broad rewrites, generator contamination, and source/projection confusion.

Template paths follow domain and lifecycle role. Platform compatibility is
declared through manifest exposures, not template directory names.
