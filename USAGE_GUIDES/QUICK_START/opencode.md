# OpenCode Quick Start

Use OpenCode for manifest-declared skills currently exposed to its `/skills` surface.

## Intended Workspace Skills

- `zyc`: runtime character skill.
- `style-doctor`: runtime drift diagnosis.

## Current Discovery Check

Use:

```powershell
opencode debug paths
opencode debug skill
```

The important question is whether `/skills` lists `style-doctor` and `zyc`.

Current `/skills` loading surface:

```text
workspace_manifest.yaml -> platform_roots.opencode
```

## Common Tasks

- Natural ZYC discussion: copy `PROMPT_TEMPLATES/character-system/runtime/zyc.md#natural-discussion`.
- Use ZYC: copy `PROMPT_TEMPLATES/character-system/runtime/zyc.md`.
- Safe text-only drift diagnosis: copy `PROMPT_TEMPLATES/character-system/engineering/diagnosis/style-doctor.md#safe-text-only-diagnosis`.
- Diagnose drift: copy `PROMPT_TEMPLATES/character-system/engineering/diagnosis/style-doctor.md`.
- Prepare handoff to maintainer: copy the handoff section in `PROMPT_TEMPLATES/character-system/engineering/diagnosis/style-doctor.md`.

## Current Boundary

`character-generator` and `character-maintainer` are not currently exposed to
OpenCode. That is a deployment choice, not a platform ownership rule.
