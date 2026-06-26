# Common Tasks

Choose by skill role first, then confirm a current platform exposure in `workspace_manifest.yaml`. Platform visibility never expands the skill's authority.

## Generate A Character

1. Prepare corpus under `<workspace-root>\packages\character-system\engineering\generation\character-generator\corpus\<character_id>`.
2. Prepare config under `<workspace-root>\packages\character-system\engineering\generation\character-generator\configs\<character_id>.json`.
3. Use `PROMPT_TEMPLATES/workflows/generate_character.md`.

Resolve `<workspace-root>` from `workspace_manifest.yaml -> workspace.source_of_truth`.

## Use A Character

1. Confirm that the character skill has a working exposure on the platform you
   intend to use.
2. Use `PROMPT_TEMPLATES/character-system/runtime/zyc.md` or the generated character's own instructions.

## Diagnose Drift

1. Capture failed output excerpt.
2. Capture expected direction.
3. Use `PROMPT_TEMPLATES/workflows/diagnose_runtime_drift.md`.

## Patch Drift

1. Give the diagnosis or handoff packet to `character-maintainer`.
2. Use `PROMPT_TEMPLATES/workflows/patch_existing_character.md`.
3. Validate with `PROMPT_TEMPLATES/workflows/validate_patch.md`.

## Consider Generator Generalization

Only after maintainer validation, use `PROMPT_TEMPLATES/workflows/generator_generalization.md`.
