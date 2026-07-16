# PROJECT_CONTEXT

`PROJECT_CONTEXT/` is the active task memory layer for this workspace. It gives humans and compatible maintenance agents a fast way to understand current task status, active decisions, and how a later session should continue work.

## What This Is

- An active task memory layer.
- A session handoff entry point.
- A current-state summary.
- A decision record index.
- A lightweight task continuity ledger.
- A planning surface for future work.

## What This Is Not

- Not the machine-readable source of truth. That remains `workspace_manifest.yaml`.
- Not the architecture or scope reference. That is now `ARCHITECTURE.md`.
- Not the style guide. That is now
  `WORKSPACE_ENGINEERING/skill_engineering/style_alignment.md`.
- Not the protocol index. Workspace protocols are indexed by `shared/INDEX.md`;
  package protocols are indexed inside each package.
- Not a protocol layer. Protocol rules live in root or package-local `shared/`.
- Not a generated report layer. Snapshots live in `reports/`.
- Not the runtime event ledger. Runtime drift records live in `packages/character-system/reports/runtime-loop/`.
- Not a skill implementation.

## Layer Relationship

- `workspace_manifest.yaml`: machine-readable source of truth for roots, skill roles, authority, execution modes, exposures, projections, protocols, and portability metadata.
- `shared/`: workspace-global governance protocol layer.
- `packages/character-system/shared/`: character-system protocol layer.
- `reports/`: snapshot layer.
- `packages/character-system/reports/runtime-loop/`: durable runtime event tracking layer.
- `ARCHITECTURE.md`: workspace scope and physical architecture reference (replaces former `PROJECT_CONTEXT/architecture.md` and `PROJECT_CONTEXT/workspace_purpose.md`).
- `PROJECT_CONTEXT/`: active task memory layer (task ledger, registry, status, todo, session handoff).
- `packages/`: related skill families organized by domain and lifecycle role.
- `skills/`: standalone skills with no package-local business protocol dependency.
- `PROJECT_CONTEXT/task_registry.yaml`: task routing layer that limits required context before broad discovery.
- `PROJECT_CONTEXT/context_budget.md`: context budget layer that controls when to expand beyond required files.
- `PROJECT_CONTEXT/task_ledger/`: lightweight maintenance ledger, partitioned by year/month; read its newest entries before reconstructing history.
- `PROJECT_CONTEXT/task_records/`: tracked, machine-readable task-outcome facts.
- `PROJECT_CONTEXT/change_surface_policy.md`: decision rules for comparing alternative writable file sets.
- `PROJECT_CONTEXT/knowledge_registry.yaml`: topic index for current context, enforceable policy, and reusable engineering knowledge.
- `PROJECT_CONTEXT/doc_pair_registry.yaml`: lightweight registry for Markdown files or directories whose same-name `.zh-CN.md` companions should be checked when edited.
- `PROJECT_CONTEXT/potential_for_future/`: low-status registries for potential improvements and risks that are not active todo items or enforceable policy.

## Recommended Reading Order For New Sessions

1. Read root `ARCHITECTURE.md` (workspace scope and physical architecture).
2. Read root `AGENTS.md` (agent startup instructions).
3. Run `git status --short --untracked-files=all`.
4. Run `python scripts/resolve_task_context.py --list` if the task id is unknown.
5. Run `python scripts/resolve_task_context.py <task-id>`.
6. Read only the returned required files.
7. Read recent task-ledger entries only when continuity matters.
8. Expand optional context only from evidence.
9. When several plausible owning layers remain, run `python scripts/workspace_cli.py changes plan <task-id> --intent <intent>`.
10. Use `python scripts/workspace_cli.py knowledge find "<topic>"` when a needed knowledge entry is not already routed by the task.
11. For Markdown edits, check `PROJECT_CONTEXT/doc_pair_registry.yaml` instead of scanning broadly for translation companions.
12. When a reusable improvement or structural risk is noticed but not yet actionable, check or update `PROJECT_CONTEXT/potential_for_future/`.

## Minimum Maintenance Workflow

Every future maintenance pass should:

1. Read the project context entry files.
2. Check `git status --short`.
3. Resolve paths through `workspace_manifest.yaml`.
4. Resolve the task with `scripts/resolve_task_context.py`.
5. Apply the returned token budget before expanding context.
6. Read recent `PROJECT_CONTEXT/task_ledger/` entries when continuity matters.
7. Load the task's required context before optional context.
8. Edit the narrowest owning layer.
9. Run the relevant validation or dry-run.
10. Update PROJECT_CONTEXT when decisions, risks, next steps, or continuity change.

When adding a new skill, first decide whether it belongs as an existing-domain skill, a new package/domain, a standalone skill, or a separate workspace. Do not force unrelated business rules into top-level `shared/`.

## What To Update Here

Update `PROJECT_CONTEXT/` when:

- a governance phase finishes;
- a major architectural decision is made;
- known risks change;
- a new validation layer or operating loop is added;
- a new skill/package boundary is introduced;
- a new lightweight routing, pair-sync, or improvement-options registry is added;
- a future session needs clear handoff context.

## What Not To Put Here

Do not put:

- copied shared protocol text;
- generated report contents pasted wholesale;
- private corpus material;
- runtime packet instances that belong in `packages/character-system/reports/runtime-loop/`;
- machine-readable registry data that belongs in the manifest or protocol manifest.

Do not use `PROJECT_CONTEXT/task_ledger/` as a replacement for reports or Git history. It is an index of remembered decisions, not the evidence itself.
