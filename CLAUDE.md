# Workspace Agent Instructions

@AGENTS.md

@shared/claude/policies/model-routing-policy.md

## Claude Code

- Use the workspace task resolver and CLI exactly as described in `AGENTS.md`.
- Treat `.claude/project-boundary.json` and `.claude/rules/` as the Claude-specific workspace boundary.
- This workspace is not the CNN project. Use `claude-project cnn` before any CNN work.
- This workspace is not the ztemp project. Use `claude-project ztemp` before any ztemp work.
- Direct `claude` startup from the target repository root is supported; do not
  switch repositories inside an already-running Claude session.
- If a boundary hook blocks native editing, restart in the correct repository
  instead of bypassing it with shell-based file rewriting.
- Treat Claude auto memory as local convenience only; durable decisions belong in the tracked workspace sources.
- Before continuing another agent's work, confirm the current branch, its merge base with `main`, and the working-tree state.
