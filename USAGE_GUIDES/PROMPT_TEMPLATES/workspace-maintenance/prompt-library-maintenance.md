# Prompt Library Maintenance

Use this prompt when extending the workspace prompt library itself.

## Foundation Task

```text
Task:
Improve the workspace prompt library without changing task authority,
workspace governance, model configuration, or platform settings.

Start here:
- `USAGE_GUIDES/PROMPT_LIBRARY.md`
- `USAGE_GUIDES/prompt_registry.yaml`
- `USAGE_GUIDES/PROMPT_TEMPLATES/README.md`
- `PROJECT_CONTEXT/todo/README.md`
- latest entries in `PROJECT_CONTEXT/tasks/ledger/README.md`

Goal:
Add or refine prompt ids and copy-ready templates so common AI maintenance work
can reuse stable instructions instead of regenerating long prompts.

Guardrails:
- Keep prompt ids small and stable.
- Prefer `prompt_frame` for short routing guidance.
- Prefer template files for copy-ready prompts or multi-anchor variants.
- Do not duplicate task registry authority in prompt text.
- Do not imply that a prompt grants write scope, tool access, model access, or
  permission to bypass Git checks.
- Validate that registered template paths exist.
- Do not commit unless explicitly asked.
```

## Acceptance Checks

Run focused checks after changing prompt library files:

```powershell
workspace prompt list
workspace prompt show prompt_library_maintenance --include-template
python scripts/resolve_task_context.py --prompt-id prompt_library_maintenance --include-template
git diff --check
```

If task routing or validation behavior changes, use the matching workspace task
route before editing scripts.
