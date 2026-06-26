# Safety Guardrails

This is a compact checklist for using the workspace skills without damaging source structure or skill boundaries.

## Core Rules

- Edit source under `workspace_manifest.yaml -> workspace.source_of_truth`, not platform projection folders.
- Use authorized or public corpus material only.
- Do not ask generated characters to impersonate real people.
- Do not let `style-doctor` patch files directly.
- Do not let `character-maintainer` rewrite a whole character unless explicitly requested.
- Do not let `character-maintainer` directly modify `character-generator`.
- Do not generalize ZYC-specific lessons into generator defaults without a generalization note.
- When using weaker or less instruction-following models, prefer text-only diagnosis and explicit review over file writes.
- Review diffs before committing.

## When In Doubt

Ask for:

```text
Diagnose first. Patch only the smallest responsible surface. Show the proposed diff before commit.
```
