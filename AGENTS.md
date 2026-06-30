# Agent Instructions

## Task Startup

1. Run `git status --short --untracked-files=all`.
2. Select an exact task id. Use `python scripts/resolve_task_context.py --list` when needed.
3. Run `python scripts/resolve_task_context.py <task-id>`.
4. Supply placeholders with `--bind name=value`; do not search broadly to guess them.
5. Obey the returned tool policy, then read required context first. Expand with `--include-optional` only from evidence.
6. Run routed validation and `workspace workflow check <task-id>`.
7. Before handoff, check knowledge writeback: record reusable lessons in the
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
- Put external deliverables under `workspace_manifest.yaml -> output_roots.workspace`; keep repo-native artifacts in source.
- Do not broadly traverse archives, private corpus, `.git/`, whole drives, junction targets, or gitignored payloads.
- Avoid `external-skills/`, `mcp/servers/`, `mcp/downloads/`, and `mcp/logs/` unless a task names them or uses that payload as a tool.
- Platform exposure grants visibility, not authority. Obey each skill's manifest role, authority, and execution modes.
- Before non-Codex/Claude writes, run `workspace agent check`; denied structural work becomes a request or isolated-worktree lease.
- Verify non-default work with `--agent` and active `--skill`; task scope alone grants no authority.
- Reports are snapshots. Prefer manifest for paths, `shared/` for policy, source for behavior, and Git for contents.
- Before moving Claude/OpenCode-used source, follow `shared/session_continuity_policy.md`.

## Routed Knowledge

- `PROJECT_CONTEXT/`: memory and handoff context.
- `shared/`: workspace-global protocols.
- `packages/<package-id>/shared/`: package protocols.
- `WORKSPACE_ENGINEERING/`: reusable methodology; read for architecture/methodology work.
- `USAGE_GUIDES/`: prompt and invocation guidance; resolve prompt ids with `--list-prompts` or `--prompt-id`.

Knowledge writeback is a check, not a quota; most routine edits are not applicable.

For style evaluation, keep checks for factual drift, privacy, safety, evidence,
maintainability, and over-stylization. Before adding a skill, confirm its
package/domain or workspace boundary.
