# Character Skill Spec

This document defines the standard structure for character skills in this workspace.

## Required Structure

```text
characters/<character_id>/
  SKILL.md
  README.md
  references/
  prompts/
  reports/
  tests/
```

## Required Files

- `SKILL.md`: runtime entry, trigger conditions, boundaries, resource routing, and safety notes.
- `README.md`: human-facing maintenance notes, usage, packaging, and update workflow.
- `references/voice_card.md`: compact voice rules and identity-safe style summary.
- `references/style_profile.md`: fuller style analysis.
- `references/writing_patterns.md`: recurring craft moves.
- `references/sentence_and_rhythm.md`: sentence length, pauses, cadence, and paragraph motion.
- `references/imagery_and_themes.md`: image systems and thematic constraints.
- `references/anti_patterns.md`: things the character skill must avoid.
- `references/evaluation_rubric.md`: scoring criteria for review.
- `references/task_recipes.md`: task-specific guidance.
- `prompts/`: reusable task prompts.
- `reports/`: build, diagnosis, and maintenance reports.

## Source Rules

- Do not include private raw corpus in Git.
- Do not impersonate a real person.
- Do not copy protected source passages into generated outputs.
- Keep character behavior style-inspired and transformation-oriented.

## Runtime Rules

A character skill should load only the references needed for the active task. Prefer compact routing through `SKILL.md`, then task-specific reference files.

Runtime character skills use role `runtime_character` and authority `runtime_output_only`. Platform exposure does not grant diagnosis, ledger, patch, or self-maintenance authority.

## Maintenance Rules

Changes should be patch-first:

- Diagnose the failed layer.
- Patch the smallest affected file.
- Preserve working examples.
- Record the reason for the change.
