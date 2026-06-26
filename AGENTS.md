# Agent Instructions

## Task Startup

1. Run `git status --short --untracked-files=all`.
2. Select an exact task id. Use `python scripts/resolve_task_context.py --list` when needed.
3. Run `python scripts/resolve_task_context.py <task-id>`.
4. Supply placeholders with `--bind name=value`; do not search broadly to guess them.
5. Obey the returned tool policy, then read required context first. Expand with `--include-optional` only from evidence.
6. Run routed validation and `workspace workflow check <task-id>`.

When multiple owning layers or file sets could satisfy the task,
run `python scripts/workspace_cli.py changes plan <task-id> --intent <intent>`
before editing. Compare named `--option` sets; skip when one target is obvious.

For status, reusable methodology, or policy not returned by resolution, use
`python scripts/workspace_cli.py knowledge find "<topic>"`. Read only the
needed results; do not scan indexed layers broadly.

The resolver consumes both registries. Reread them only when editing them or
resolution fails. On failure, read the context README/status, manifest, target,
and nearest policy.

## Always-On Boundaries

- Treat `workspace_manifest.yaml -> workspace.source_of_truth` as source. Never maintain source through platform projections.
- Preserve existing user changes. Do not commit unless requested.
- Keep transient files in `AI_TOOL_STAGING_DIR`, or the invoking tool's `${DATA_ROOT}\<tool>\cache\staging`; remove them after use.
- Put workspace-task external deliverables under `workspace_manifest.yaml -> output_roots.workspace`; keep repository-native artifacts in source and follow `shared/delivery_output_policy.md`.
- Do not broadly traverse archives, private corpus, `.git/` internals, whole drives, or junction targets without explicit task approval.
- Platform exposure grants visibility, not authority. Obey each skill's manifest role, authority, and execution modes.
- Before non-Codex/Claude writes, run `workspace agent check`; denied
  structural work becomes a request or isolated-worktree lease, never
  self-registration or projection edits.
- Verify non-default work with `--agent` and active `--skill`; task scope alone
  grants no authority.
- Reports are snapshots. Prefer manifest for paths and protocol routing, root or package-local `shared/` for policy, source files for behavior, and current Git state for repository contents.
- Before moving a source directory used by Claude Code or OpenCode, follow `shared/session_continuity_policy.md` and preserve external session backups plus old-to-new path mappings.

## Routed Knowledge

- `PROJECT_CONTEXT/`: current memory and handoff context.
- `shared/`: enforceable workspace-global protocols.
- `packages/<package-id>/shared/`: enforceable domain protocols for package members.
- `WORKSPACE_ENGINEERING/`: reusable AI workspace methodology, with Skill Engineering as a subdomain; read only for architecture or methodology work.
- `USAGE_GUIDES/`: prompt and invocation guidance; resolve prompt ids with `--list-prompts` or `--prompt-id`.

For style evaluation, preserve independent checks for factual drift, privacy, safety, evidence, maintainability, and over-stylization. Before adding a skill, confirm its package/domain or workspace boundary instead of expanding top-level `shared/` by default.
