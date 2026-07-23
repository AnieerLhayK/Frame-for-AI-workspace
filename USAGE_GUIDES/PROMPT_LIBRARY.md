# Prompt Library

This is the stable entry point for the workspace prompt library.

The library is not a separate runtime service. It is a governed usage layer made
from:

- `USAGE_GUIDES/prompt_registry.yaml`: prompt ids, metadata, and template paths.
- `USAGE_GUIDES/PROMPT_TEMPLATES/`: copy-ready prompt bodies.
- `scripts/resolve_task_context.py --prompt-id`: direct prompt resolution.
- `workspace prompt list` and `workspace prompt show`: user-facing CLI access.

## Purpose

Use the prompt library to reduce repeated meta-prompt reconstruction during AI
maintenance work. The intended savings are practical and bounded:

- prefer a known prompt id over rewriting the same task instructions;
- load full templates only when the prompt will actually be copied or edited;
- keep high-risk guardrails inside reusable templates;
- keep task routing, write scope, and authority checks outside prompt text.

The library does not replace `PROJECT_CONTEXT/tasks/registry/index.yaml`,
`PROJECT_CONTEXT/governance/context_budget.md`, shared protocols, or model authority
boundaries.

## Current Maturity

| Area | State | Notes |
| --- | --- | --- |
| Registry | Usable | Prompt ids can be listed and resolved. |
| Template loading | Usable | `--include-template` loads full files or anchors on demand. |
| Character-system prompts | Usable | Existing templates cover generation, maintenance, diagnosis, and ZYC use. |
| Workspace maintenance prompts | Building | Core branch, handoff, health, and scoped-change templates are the first priority. |
| Search and discovery | Early | Use list/show today; keyword search can come later. |
| Quality scoring | Planned | Entries need coverage, specificity, and token-cost review. |

## Prompt Families

| Family | Purpose | Preferred Shape |
| --- | --- | --- |
| Workspace maintenance | Routine source-tree maintenance, health triage, branch handling, scoped change planning, and handoff continuation. | Copy-ready templates with explicit Git and write-scope guardrails. |
| Governance and authority | Agent, model-routing, workspace boundary, and policy changes. | Short prompt frames unless a repeated workflow needs a full template. |
| Reports and validation | Report freshness, health remediation, protocol checks, and validation routing. | Copy-ready templates when command order matters. |
| Skills and packages | Skill generation, diagnosis, maintenance, release packaging, and standalone skill publishing. | Existing character-system templates plus future package/release prompts. |
| Platform exposure | Codex, Claude Code, OpenCode, Hermes, projections, and local loading surfaces. | Templates only for repeated debug workflows; otherwise use task routing. |

Do not add a family merely to mirror repository folders. Add it only when it
helps a user or agent choose a smaller prompt without rereading broad docs.

## Commands

List available prompt ids:

```powershell
workspace prompt list
```

Show a prompt frame or template reference:

```powershell
workspace prompt show <prompt-id>
```

Show the full copy-ready template only when needed:

```powershell
workspace prompt show <prompt-id> --include-template
```

Resolve through the underlying script when debugging:

```powershell
python scripts/resolve_task_context.py --prompt-id <prompt-id> --include-template
```

## First Workspace Maintenance Prompts

| Prompt id | Use when |
| --- | --- |
| `prompt_library_maintenance` | Extending this library itself. |
| `workspace_health_remediation` | `workspace health` reports NEEDS_ATTENTION or FAIL. |
| `scoped_change_planning` | One request could touch several owning layers. |
| `task_handoff_continuation` | Continuing from a handoff or previous session. |
| `branch_merge_review` | Reviewing a branch before merging into `main`. |

Example:

```powershell
workspace prompt show workspace_health_remediation --include-template
```

## Library Shape

Each durable prompt should have:

- a stable prompt id in `prompt_registry.yaml`;
- a short purpose;
- a type such as `maintenance_meta`, `copy_ready_template`, or
  `workflow_template`;
- either a small `prompt_frame` or a `template_path`;
- clear guardrails for scope, authority, and non-goals;
- a token cost visible through `workspace prompt show`.

Use a small `prompt_frame` when the task only needs routing guidance. Use a
template file when the prompt is copy-ready, longer than a few bullets, or needs
anchors for multiple variants.

## Quality Checklist

Before adding or promoting a prompt, check:

- The prompt names the task boundary and the first files or commands to inspect.
- It says what not to change.
- It keeps model choice, write scope, tool access, and Git authority separate.
- It can be resolved with `workspace prompt show <prompt-id> --include-template`.
- It is shorter than the ad hoc prompt it replaces.
- It points to task routing instead of duplicating task registry policy.

## Development Branch

The long-lived branch for this module is:

```text
codex/prompt-library-foundation
```

Keep this branch focused on making the existing prompt registry and templates
discoverable, complete, and cheap to use. Merge back to `main` only after the
library has enough coverage, validation, and documentation to replace ad hoc
prompt reconstruction in ordinary workspace maintenance.

## Next Build Phases

1. Inventory high-frequency workspace maintenance tasks.
2. Convert repeated maintenance prompts into copy-ready templates.
3. Add prompt ids for the new templates.
4. Improve quick-start documentation so users can find the library quickly.
5. Add lightweight validation for missing template paths and duplicate ids.
6. Consider `workspace prompt find <keyword>` only after the library has enough
   entries to make search useful.
