# Patch Protocol

This protocol defines how `style-doctor` hands a diagnosis to `character-maintainer`.

## Roles

- `style-doctor`: diagnose runtime failure and propose a narrow patch.
- `character-maintainer`: decide, apply, validate, and record the patch.
- character skill: remains the source artifact being patched.

## Authority Boundary

`style-doctor` output is advisory until maintainer review. It may produce diagnosis and handoff records, but it must not:

- edit character, generator, maintainer, shared, or manifest source files;
- write patch notes, validation notes, or generalization notes;
- update the patch ledger;
- assign `accepted`, `rejected`, `deferred`, `applied`, or `validated` status.

`character-maintainer` owns those decisions and records. If `style-doctor` includes candidate wording, treat it as suggested text, not as an approved patch.

Recommended file targets in handoffs should be workspace-relative source paths. Do not use platform projection paths as patch targets.

## Handoff Payload

Every diagnosis should include:

```text
character_id:
source_context:
runtime_input:
runtime_output:
user_feedback:
drift_type:
failed_layer:
evidence:
recommended_patch:
files_to_touch:
files_not_to_touch:
validation_plan:
version_note:
```

When the handoff becomes a durable runtime-loop record, include the packet IDs and paths:

```text
diagnosis_id:
diagnosis_record_path:
handoff_id:
handoff_record_path:
```

Do not rely on fixed filenames or "latest" files. `style-doctor` must create unique diagnosis/handoff records, and `character-maintainer` must retrieve them by explicit path, ID, or ledger lookup before deciding whether to patch.

## Failed Layer Values

Use one or more:

- `SKILL.md`
- `references/voice_card.md`
- `references/style_profile.md`
- `references/writing_patterns.md`
- `references/sentence_and_rhythm.md`
- `references/imagery_and_themes.md`
- `references/anti_patterns.md`
- `references/evaluation_rubric.md`
- `references/task_recipes.md`
- `prompts/*`

## Patch Rules

- Prefer the smallest change that explains the failure.
- Do not rewrite the whole character skill for one drift instance.
- Preserve strong existing examples.
- Add anti-patterns only when the failure is repeatable.
- Update prompts only when routing or instruction pressure caused the failure.

## Maintainer Response

`character-maintainer` should return:

```text
accepted:
patch_summary:
files_changed:
validation_result:
version_record:
follow_up:
```
