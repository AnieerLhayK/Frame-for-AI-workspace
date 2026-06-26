# Codex Quick Start

Use Codex for any manifest-declared skill currently exposed to its loading surface.

## Available Workspace Skills

- `character-generator`: generate initial character skills from authorized corpus and config.
- `character-maintainer`: patch and evolve existing character skills.
- `zyc`: runtime ZYC-inspired writing and discussion with text-only authority.

## Local Loading

Expected local loading surface:

```text
workspace_manifest.yaml -> platform_roots.codex
```

Workspace source remains:

```text
workspace_manifest.yaml -> workspace.source_of_truth
```

The preferred setup is the manifest-declared Codex projections under `workspace_manifest.yaml -> projections[]`.

## Common Tasks

- Generate new character: copy `PROMPT_TEMPLATES/character-system/engineering/generation/character-generator.md`.
- Quick patch from diagnosis: copy `PROMPT_TEMPLATES/character-system/engineering/maintenance/character-maintainer.md#quick-patch-from-diagnosis`.
- Patch existing character: copy `PROMPT_TEMPLATES/character-system/engineering/maintenance/character-maintainer.md`.
- Validate patch: copy `PROMPT_TEMPLATES/workflows/validate_patch.md`.
- Review generator generalization: copy `PROMPT_TEMPLATES/workflows/generator_generalization.md`.
- Use ZYC: copy `PROMPT_TEMPLATES/character-system/runtime/zyc.md`; the folder name records its original guide grouping, not platform ownership.

Platform exposure does not widen a skill's manifest authority. In particular, invoking `zyc` from Codex remains `text_only`.
