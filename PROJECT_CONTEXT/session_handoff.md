# Session Handoff

## One-Line Summary

This workspace is a manifest-driven skill monorepo with package, standalone
skill, protocol, and platform-projection boundaries.

## Current Source Root

`workspace_manifest.yaml -> workspace.source_of_truth`

## Most Important Rules

- Treat `workspace_manifest.yaml` as the machine-readable source of truth.
- Treat root `shared/` as workspace governance and package-local `shared/` as domain protocols.
- Treat `reports/` as snapshots, not truth.
- Treat `packages/character-system/reports/runtime-loop/` as runtime event tracking.
- Treat `PROJECT_CONTEXT/` as long-term memory and handoff context.
- Do not edit through platform loading surfaces declared under `workspace_manifest.yaml -> platform_roots`.
- Do not infer skill authority from its source directory or invoking platform.
- Treat `skills[].exposures[]` as visibility declarations, not permission grants.
- Before any source path migration, run `workspace sessions audit` and preserve
  the mappings in `PROJECT_CONTEXT/session_migrations.json`.
- Treat old projection roots in historical reports or prompts as stale until confirmed against `workspace_manifest.yaml`.
- Do not copy shared protocols into skills.
- Do not rebuild junctions unless explicitly asked.
- Do not generalize ZYC-specific lessons into generator templates without maintainer approval.

## Recently Completed Work

- Task and prompt registries, context budgets, and exact token measurement.
- Change-surface planning and bounded knowledge lookup.
- Report freshness, failure diagnostics, health checks, and governance summaries.
- A user-level `workspace` launcher for the developer interface.
- Claude Code startup compatibility through root `CLAUDE.md -> AGENTS.md`.
- Tracked Claude project rules and write guards under `.claude/`.
- Explicit `claude-workspace` and `claude-cnn` launchers backed by a machine-local project registry.
- Platform exposure represented by `skills[].exposures[]`, `platform_roots`, and `projections[]`.
- Character skills grouped under `packages/character-system/` by runtime and
  engineering role, with domain protocols moved into package-local `shared/`.
- `skills/` reserved for unrelated standalone skills.
- External Claude/OpenCode session backups and a read-only continuity audit for
  the character-package migration.

## Next Recommended Steps

1. Run `git status --short --branch`.
2. Run `workspace summary` and confirm the branch is based on current `main`.
3. Resolve the exact task before reading optional context.
4. Continue the active feature branch or create a fresh branch from `main`.
5. Run the routed validation and `workspace health --with-tests` before handoff.

For Claude Code, use `claude-workspace` for this repository. If the request is
for CNN work, stop and use `claude-cnn`; do not create a CNN directory here.

## Do Not Do

- Do not move package or skill directories without an explicit architecture task.
- Do not rebuild links or junctions as part of context maintenance.
- Do not modify character-generator core logic.
- Do not modify character-maintainer patch logic.
- Do not modify style-doctor diagnosis logic.
- Do not modify ZYC style content.
- Do not treat old reports as current truth without checking headers.

## First Files To Read In A New Session

1. Root `AGENTS.md` through the agent's native startup file.
2. `git status --short --branch`
3. `python scripts/resolve_task_context.py --list` when the task id is unknown.
4. `python scripts/resolve_task_context.py <task-id>`
5. Only the required files returned by the resolver.
6. The latest 5 ledger entries only when continuity is needed.

## Skill Expansion Rule

Before adding a new skill, decide whether it belongs in the current character-system area, a new package/domain inside this workspace, a standalone skill area, or a separate workspace. Warn the user when a skill looks misplaced, and propose a package/domain structure instead of forcing unrelated rules into top-level `shared/`.

## Conflict Resolution

If context conflicts:

1. Prefer `workspace_manifest.yaml` for paths, registry, projections, and portability metadata.
2. Prefer `shared/` for protocols and policies.
3. Prefer current Git state for actual repository contents.
4. Prefer current generated reports only after checking their snapshot headers.
5. Treat `PROJECT_CONTEXT/` as orientation, not authority.
