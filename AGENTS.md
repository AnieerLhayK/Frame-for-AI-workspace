# Agent Instructions

## Task Startup

1. Run `git status --short --untracked-files=all`.
2. Select an exact task id. Use `python scripts/resolve_task_context.py --list` when needed.
3. Run `python scripts/resolve_task_context.py <task-id>`.
4. Before any workspace or workspace-mediated external write, start one task
   record: `workspace records start --task-type <task-id> --operation workspace_write`.
   Add `--operation external_write` when the task will mutate an approved
   external target, and export its returned id as `WORKSPACE_TASK_RECORD` for
   platform write adapters. Pure read-only work is exempt.
5. Supply placeholders with `--bind name=value`; do not search broadly to guess them.
6. Obey the returned tool policy, then read required context first. Expand with `--include-optional` only from evidence.
7. Run routed validation and `workspace workflow check <task-id> --record-id <TASK-ID>` while the record is active; finalize the record afterwards.
8. Before handoff, check knowledge writeback: record reusable lessons in the
   smallest relevant `WORKSPACE_ENGINEERING/` entry, or say not applicable.

If multiple layers could satisfy the task, run
`python scripts/workspace_cli.py changes plan <task-id> --intent <intent>`;
skip only when one target is obvious.

For status, methodology, or policy not returned by resolution, use
`python scripts/workspace_cli.py knowledge find "<topic>"`; read only needed hits.

The resolver consumes both registries. Reread them only when editing them or on
resolution failure; then read the context README/status, manifest, target, and
nearest policy.

## Always-On Boundaries

- Treat `workspace_manifest.yaml -> workspace.source_of_truth` as source; never maintain through projections.
- Preserve existing user changes. Do not commit unless requested.
- Keep transient files in `AI_TOOL_STAGING_DIR` or tool staging; remove after use.
- Put external deliverables in `output_roots.workspace`; keep source artifacts in source.
- Do not broadly traverse archives, private corpus, `.git/`, whole drives, junction targets, or gitignored payloads.
- External skill intake: follow `shared/workspace_policy.md`.
- Avoid `mcp/servers/`, `mcp/downloads/`, and `mcp/logs/` unless a task names them or uses that payload as a tool.
- Platform exposure grants visibility, not authority. Obey each skill's manifest role, authority, and execution modes.
- Before non-Codex/Claude writes, run `workspace agent check`; denied structural work becomes a request or isolated-worktree lease.
- Every write gate must receive an active task record ID. Use
  `workspace agent check ... --record-id <TASK-ID>`; do not reuse a completed
  record or an unregistered historical record for new work.
- Verify non-default work with `--agent` and active `--skill`; task scope alone grants no authority.
- Reports are snapshots. Prefer manifest for paths, `shared/` for policy, source for behavior, and Git for contents.
- Before moving Claude/OpenCode-used source, follow `shared/session_continuity_policy.md`.
- For Markdown edits, check `PROJECT_CONTEXT/doc_pair_registry.yaml`; update registered same-name `.zh-CN.md` companions when they exist, or record why no semantic sync is needed. When creating a new `.zh-CN.md`, update that registry in the same change.
- Record reusable guidance in its owning rule or `PROJECT_CONTEXT/potential_for_future/optimization_options.yaml`.

## Ignore Rule Ownership

- Put a new ignore rule in the narrowest directory that owns the generated,
  local, or private artifact. Do not add a root rule for a path that belongs to
  one independently managed subtree.
- Keep workspace-wide rules in the root `.gitignore`: shared caches, temporary
  files, environment files, OS artifacts, generic build/package outputs,
  private source drops, and patterns intentionally spanning multiple trees
  such as `**/reports/corpus_stats.md`.
- Put Claude-local state and the `.claude/skills/` projection under
  `.claude/.gitignore`; put MCP runtime/install buckets under `mcp/.gitignore`;
  put historical report metadata under `reports/.gitignore`.
- Keep a standalone skill or independently publishable package's artifact
  rules in that source tree's own `.gitignore` when the rules are specific to
  that skill or package. Existing nested skill `.gitignore` files are the
  source of truth for those publishability boundaries.
- Preserve tracked exceptions such as `.claude/settings.json`,
  `mcp/README.md`, and `mcp/configs/*.json`. Do not duplicate a child rule in
  the root unless the same pattern is intentionally needed elsewhere.
- Before and after changing ownership, verify representative ignored and
  visible paths with `git check-ignore -v --no-index -- <path>` and run the
  routed task validation.

## Routed Knowledge

- `PROJECT_CONTEXT/`: memory and handoff context.
- `shared/`: workspace-global protocols.
- `packages/<package-id>/shared/`: package protocols.
- `WORKSPACE_ENGINEERING/`: reusable methodology; read for architecture/methodology work.
- `USAGE_GUIDES/`: prompt and invocation guidance; resolve prompt ids with `--list-prompts` or `--prompt-id`.
- `PROJECT_CONTEXT/doc_pair_registry.yaml`: lightweight Markdown zh-CN companion registry.
- `PROJECT_CONTEXT/potential_for_future/`: low-status future options and risk registers, not active todo or enforceable policy.

Knowledge writeback is a check, not a quota; most routine edits are not applicable.

For style evaluation, keep checks for factual drift, privacy, safety, evidence,
maintainability, and over-stylization. Before adding a skill, confirm its
package/domain or workspace boundary.
