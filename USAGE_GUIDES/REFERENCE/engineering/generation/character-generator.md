# character-generator Reference

## Purpose

`character-generator` creates initial platform-neutral character skill packages from authorized corpus material and a config JSON.

## Inputs

- Corpus directory: `corpus/<character_id>`
- Config file: `configs/<character_id>.json`
- Required config fields include `character_id`, `display_name`, `corpus_path`, `output_path`, `language`, `privacy_level`, `style_strength`, `target_tasks`, and `forbidden_tasks`.

## Command

```powershell
cd <workspace-root>\packages\character-system\engineering\generation\character-generator
python scripts\build_character.py --config configs\<character_id>.json
```

Resolve `<workspace-root>` from `workspace_manifest.yaml -> workspace.source_of_truth`.

## Output

```text
characters/<character_id>/
  SKILL.md
  README.md
  references/
  prompts/
  reports/
  output_manifest.json
```

## Boundaries

- It creates initial structure.
- It can scaffold bounded chat/discussion support when `discussion` is in `target_tasks`.
- It does not maintain mature characters.
- It does not absorb one-off ZYC evolution without maintainer-approved generalization.
