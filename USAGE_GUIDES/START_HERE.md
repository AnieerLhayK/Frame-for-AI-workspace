# Start Here

Most users should start by copying a prompt template.

## Fastest Copy Prompts

For everyday use, start with these short templates before reading the longer reference material:

- ZYC natural discussion: `PROMPT_TEMPLATES/character-system/runtime/zyc.md#natural-discussion`
- ZYC rewrite: `PROMPT_TEMPLATES/character-system/runtime/zyc.md#rewrite-in-zyc-style`
- style-doctor safe diagnosis: `PROMPT_TEMPLATES/character-system/engineering/diagnosis/style-doctor.md#safe-text-only-diagnosis`
- character-maintainer patch from diagnosis: `PROMPT_TEMPLATES/character-system/engineering/maintenance/character-maintainer.md#quick-patch-from-diagnosis`

If you are maintaining the workspace rather than running a skill, start with:

```text
QUICK_START/workspace_cli.md
```

It explains the unified task, prompt, knowledge, change-planning, report, and
validation commands in beginner-friendly language.

If you are trying to reuse, find, or extend stored prompts, start with:

```text
PROMPT_LIBRARY.md
```

The direct commands are:

```powershell
workspace prompt list
workspace prompt show <prompt-id> --include-template
```

When switching Claude Code between the workspace and a separate project, read:

```text
QUICK_START/claude_code.md
```

Use `prompt_registry.yaml` when you specifically need prompt ids such as
`minimal_edit`, `platform_exposure`, or `drift_repair`.

For detailed guidance after choosing a task, open:

```text
REFERENCE/README.md
```

It separates runtime use, engineering operations, end-to-end workflows, and
platform loading notes so platform exposure is not mistaken for skill
ownership.

## I Want To Generate A New Character

Use:

```text
PROMPT_TEMPLATES/character-system/engineering/generation/character-generator.md
```

You need:

- a character id;
- a display name;
- an authorized corpus folder;
- a config JSON file;
- a target output folder.

## I Want To Fix An Existing Character

Use:

```text
PROMPT_TEMPLATES/character-system/engineering/maintenance/character-maintainer.md
```

You need:

- a target character folder;
- feedback or a diagnosis packet;
- allowed patch scope;
- do-not-touch constraints;
- a validation expectation.

## I Want To Diagnose Runtime Drift

Use:

```text
PROMPT_TEMPLATES/character-system/engineering/diagnosis/style-doctor.md
PROMPT_TEMPLATES/workflows/diagnose_runtime_drift.md
```

The output should be a diagnosis packet and, when needed, a handoff packet.

## I Want To Use ZYC

Use:

```text
PROMPT_TEMPLATES/character-system/runtime/zyc.md
```

If ZYC output drifts, diagnose first. Do not directly turn ZYC-specific fixes into generator changes.

## Role And Exposure

- Choose a skill by its role and authority, not by the directory name of its source.
- Check `workspace_manifest.yaml -> skills[].exposures[]` to see where the skill is currently discoverable.
- `zyc` is currently exposed to both Codex and OpenCode from one source folder.

Exposure is visibility, not permission. If a workflow crosses platforms, keep the skill's authority and execution-mode boundary intact.
