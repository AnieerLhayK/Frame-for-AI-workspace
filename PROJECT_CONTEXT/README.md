# PROJECT_CONTEXT

`PROJECT_CONTEXT/` is the workspace's active task-memory layer. It records
current state, decisions, continuity, and future work; it is not the source of
truth for paths, protocols, or generated reports.

## Authority map

- `workspace_manifest.yaml`: machine-readable roots, roles, authority, exposures,
  projections, protocols, and portability facts.
- `ARCHITECTURE.md`: workspace scope and physical layout.
- `shared/`: enforceable workspace protocols.
- `packages/character-system/shared/`: package-local protocols.
- `reports/`: generated or authored snapshots.
- `packages/character-system/reports/runtime-loop/`: runtime diagnosis records.
- `PROJECT_CONTEXT/`: active memory only.

## Contents

- `current_status.md`: latest verified state, open risks, and recent validation.
- `decisions.md`: durable architectural and governance decisions.
- `task_registry.yaml`: task routing and write-scope rules.
- `task_records/`: machine-readable task outcomes.
- `task_ledger/`: lightweight dated continuity index.
- `todo/`: active future work and intake queues.
- `knowledge_registry.yaml`: bounded topic index for reusable knowledge.
- `doc_pair_registry.yaml`: Markdown companion coverage rules.
- `change_surface_policy.md`: comparison rules for alternative writable surfaces.
- `potential_for_future/`: non-active risks and improvement options.

## New-session workflow

1. Read root `AGENTS.md` and run `git status --short --untracked-files=all`.
2. Resolve the exact task with `scripts/resolve_task_context.py`.
3. Read only the resolver's required context before broad discovery.
4. Start the task record before workspace or external writes.
5. Edit the narrowest owning source layer; use the manifest for paths.
6. Run routed validation and `workspace workflow check` while the record is active.
7. Update this layer only when state, decisions, risks, or continuity change.

When Markdown has a registered companion, update the existing `.zh-CN.md`
semantically. Missing companions are documented exceptions, not automatic new
files.

## Keep out

Do not copy shared policy, generated report bodies, private corpus material,
runtime packet instances, or machine-readable manifest/protocol data here.
Do not use `task_ledger/` as a replacement for reports or Git history.
