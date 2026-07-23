# PROJECT_CONTEXT

`PROJECT_CONTEXT/` is the workspace memory and routing façade. The manifest,
shared policy, source code, and generated reports remain authoritative for
their own facts.

## Startup interface

- `context_index.yaml`: machine-readable domain map and loading rules.
- `README.md` / `README.zh-CN.md`: human navigation and boundaries.
- `workspace summary` and `workspace explain`: live AI/developer summaries.

## Domains

- `continuity/`: current status, session handoff, and protected migrations.
- `governance/`: context budget and change-surface policy.
- `documentation/`: canonical Markdown companion registry.
- `memory/`: durable decisions and glossary.
- `references/`: external project boundary records.
- `tasks/`: task routing, structured records, and dated ledger.
- `knowledge/`: topic index and topic-local entries.
- `potential_for_future/`: active options and risks; terminal history is read
  only for named audits or migrations.
- `todo/`: unfinished or trigger-based work.
- `reports/`: context-local reports; `history/` is excluded from startup.

The root registry YAML compatibility projections were retired on 2026-07-19.
Use `tasks/registry/index.yaml`, `knowledge/index.yaml`, and
`documentation/doc_pair_registry.yaml` directly. Historical ledgers and
reports retain path text that was true when written, but it is not an active
route or alias.

## Workflow

1. Read root `AGENTS.md`, check Git status, and resolve the exact task.
2. Read only the resolver's required context.
3. Start a task record before workspace or external writes.
4. Edit the narrowest owning source layer and preserve manifest authority.
5. Run routed validation and `workspace workflow check` before finalizing.

Markdown edits use `PROJECT_CONTEXT/documentation/doc_pair_registry.yaml` and
update an existing `.zh-CN.md` companion when one is registered. Missing
companions remain documented exceptions.
