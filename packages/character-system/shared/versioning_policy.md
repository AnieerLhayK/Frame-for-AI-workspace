# Versioning Policy

This policy defines version records across generator, maintainer, style doctor, and character skills.

## Version Surfaces

- `character-generator`: generation logic, templates, schemas, and build scripts.
- `character-maintainer`: maintenance workflow, patch prompts, compatibility policy, and reports.
- `style-doctor`: runtime diagnosis prompts, drift taxonomy usage, and patch suggestions.
- `characters/zyc`: character-specific references, prompts, reports, and packaging scripts.

## Record Format

Each meaningful change should record:

```text
date:
component:
change_type:
summary:
reason:
files_changed:
validation:
compatibility:
follow_up:
```

## Change Types

- `generator-template`
- `generator-script`
- `maintainer-policy`
- `doctor-diagnosis`
- `character-reference`
- `character-prompt`
- `character-report`
- `workspace-link`
- `shared-protocol`

## Compatibility

When generator or shared protocol changes affect existing characters, record whether:

- no character update is required
- maintainer should patch existing characters
- style-doctor should adjust diagnosis prompts
- generated characters need regeneration

## Character Version Notes

Character-specific version notes should stay near the character, usually under `reports/` or a changelog file if one exists.

Workspace-level setup changes belong in:

```text
reports/workspace_setup_report.md
```

Workspace reports are snapshots. When a version note relies on report data, include the source commit or regenerate the report first.

Long-term narrative summaries and session handoffs belong in `PROJECT_CONTEXT/`. They should summarize decisions and continuity, not replace version records, manifests, reports, or runtime loop ledgers.
