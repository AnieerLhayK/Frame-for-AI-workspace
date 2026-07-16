# Context Budget

This file defines the default context-loading budget for maintenance work in this workspace.

It does not replace `workspace_manifest.yaml`, `shared/`, or `PROJECT_CONTEXT/task_registry.yaml`.
Use it as a budget guard before reading optional files, reports, generated outputs, archives, or platform data.

## Purpose

The workspace is large enough that reading broadly by default wastes tokens and increases the chance of following stale paths.

The budget rule is:

```text
load the smallest truth-bearing context first
then expand only when the task registry or evidence requires it
```

## Budget Levels

### Level A: Resolver Startup

Load or execute these for almost every maintenance task:

- `AGENTS.md`
- `git status --short --untracked-files=all`
- `python scripts/resolve_task_context.py <task-id>`

Use `python scripts/resolve_task_context.py --list` when the exact task id is unknown. The resolver reads the full task and prompt registries itself and emits only the selected task view.

The resolver also returns a task-level tool profile. Unlisted capabilities are denied by default; capabilities under `confirm` require explicit user approval for the current task.

Reason: this establishes routing, prompt guidance, Git safety, tool boundaries, and a measured context budget without loading the full governance layer into model context.

### Level B: Task-Required Context

Load only the files returned under `required context` by `scripts/resolve_task_context.py`.

Examples:

- platform exposure work: manifest, current status, architecture, quick starts, platform debug output;
- runtime drift work: runtime loop policy, drift taxonomy, target character `SKILL.md`;
- prompt usage work: `USAGE_GUIDES/README.md`, `START_HERE.md`, `USAGE_GUIDES/prompt_registry.yaml`, and relevant prompt templates.
- task prompt frames are returned directly by the resolver;
- use `--include-template` only when the full copy-ready template is required.

Reason: task-required context should be enough to start work safely.

The resolver normally omits these routing files from model context after consuming them:

- `PROJECT_CONTEXT/task_registry.yaml`
- `PROJECT_CONTEXT/context_budget.md`
- `USAGE_GUIDES/prompt_registry.yaml`

Tasks that maintain those files retain them explicitly.

### Level C: Optional Context

Load optional files only when one of these is true:

- required context points to a specific optional file;
- the user asks for deeper analysis;
- validation fails and the optional file can explain why;
- the task registry lists the file under `optional` and the task cannot be completed from Level A/B context.

Examples:

- `ARCHITECTURE.md`
- `PROJECT_CONTEXT/session_handoff.md`
- `WORKSPACE_ENGINEERING/`
- skill-local docs, prompts, checklists, or examples
- previous generated reports

Reason: useful context should be demand-loaded, not preloaded.

### Level D: Default Avoid

Do not read these by default:

- `reports/`
- `packages/character-system/reports/runtime-loop/` except ledgers/templates required for a runtime-loop task
- generated character outputs such as `packages/character-system/engineering/generation/character-generator/characters/`
- large skill reference folders not named by the task
- task-ledger months older than the current continuity window
- platform data roots such as `${DATA_ROOT}/`
- tool install roots such as `${WORKSPACE_ROOT}/tools/`
- raw external skill repositories under `workspace_manifest.yaml -> external_roots.raw_skills`
- gitignored local MCP payloads such as `mcp/servers/`, `mcp/downloads/`, and
  `mcp/logs/`

Read them only when the task registry or user explicitly requires them.

Reason: these are often snapshots, generated artifacts, large references, or local deployment data.

### Level E: Prohibited Without Explicit Approval

Do not read, move, delete, or traverse these without explicit task-specific approval:

- old backups or archive directories;
- private raw corpus material;
- `.git/` internals;
- platform loading surfaces as editable source;
- gitignored external skill drops and MCP payload directories during ordinary
  workspace maintenance;
- whole-drive searches;
- unbounded parent traversal;
- junction targets reached through deletion or migration commands.

Reason: these surfaces have high privacy, safety, or accidental-coupling risk.

## Expansion Rules

When more context is needed, expand in this order:

1. Same file, nearby section.
2. Same task registry entry, optional files.
3. Same owning layer, narrow file search.
4. Shared protocol named by the task.
5. Report snapshot only after checking its header.
6. Broader repository search only with a narrow pattern and path bound.

Do not expand because "the workspace might contain something relevant." Expand only from evidence.

## Read Caps

Use these soft caps unless the user asks for a full audit:

- initial orientation: Level A only;
- narrow edit: resolver startup + required files;
- medium maintenance: Level A + required + selected optional files;
- audit or migration: Level A + required + explicit user-approved path checks;
- report regeneration: read source files and generator scripts, not unrelated historical reports.

## Git Guard

Before edits:

1. Run `git status --short --untracked-files=all`.
2. Identify existing modified or untracked files.
3. Do not overwrite unexplained user changes.
4. Prefer a short-lived feature branch for governance changes, then delete it
   after the validated work is merged.

After edits:

1. Run focused validation from the task registry.
2. Run `git diff --check`.
3. Add the human decision note to the appropriate `PROJECT_CONTEXT/task_ledger/YYYY/MM/DD.md` file when the task materially changes workspace maintenance state.
4. Summarize changed files and whether the work should be committed.

## Conflict Rules

When sources disagree:

1. Prefer `workspace_manifest.yaml` for paths, registries, and local deployment facts.
2. Prefer manifest-routed root or package-local `shared/` for protocol rules.
3. Prefer current Git state for actual repository contents.
4. Prefer report snapshots only after checking their generated header.
5. Treat `PROJECT_CONTEXT/` as memory and routing, not a stronger source than manifest-routed protocols.

## Token Meter

The machine-readable thresholds live under:

```text
PROJECT_CONTEXT/task_registry.yaml -> default_rules.context_budget.token_meter
```

The root `AGENTS.md` has its own regression ceiling under `root_agents_warn_tokens`. Keep task-specific commands and explanations in resolver-owned context instead of expanding the always-loaded file.

Run:

```powershell
python scripts\resolve_task_context.py <task-id>
python scripts\resolve_task_context.py <task-id> --include-optional
python scripts\resolve_task_context.py --prompt-id <prompt-id> --include-template
```

The default mode warns rather than blocks. Use `--strict-budget` in CI or explicit audits when a warning should produce a non-zero exit code.

When `tiktoken` is installed, the meter uses the declared encoding. Otherwise it falls back to a marked heuristic that counts ASCII and non-ASCII text separately. This measures planned workspace context, not system instructions, hidden reasoning, tool schemas, or final API billing.

Run startup regressions with:

```powershell
python -m unittest scripts.tests.test_startup_context_policy
```
