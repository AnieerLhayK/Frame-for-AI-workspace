# Workspace Agent Instructions

@AGENTS.md

## Claude Code

- Use the workspace task resolver and CLI exactly as described in `AGENTS.md`.
- Treat model-routing guidance as a visible recommendation only; it must never
  edit model configuration, provider settings, plugins, or permission policy.
- Model advice is injected only by `.claude/hooks/model_routing_guard.ps1` when
  the effective toggle is enabled. `.claude/model-routing-advice.local.json`,
  when present, overrides `.claude/model-routing-advice.json`.
- If the effective toggle is disabled, do not output model-tier assessments,
  model-switch recommendations, or model-advice pauses; behave as if this
  integration is absent.
- Do not keep static model-routing templates in `CLAUDE.md`; the detailed
  policy belongs in `shared/claude/policies/model-routing-policy.md` and is
  surfaced only by the hook when enabled.
- Treat `.claude/project-boundary.json` and `.claude/rules/` as the Claude-specific workspace boundary.
- This workspace is not the CNN project. Use `claude-project cnn` before any CNN work.
- This workspace is not the ztemp project. Use `claude-project ztemp` before any ztemp work.
- Direct `claude` startup from the target repository root is supported; do not
  switch repositories inside an already-running Claude session.
- If a boundary hook blocks native editing, restart in the correct repository
  instead of bypassing it with shell-based file rewriting.
- Treat Claude auto memory as local convenience only; durable decisions belong in the tracked workspace sources.
- Before continuing another agent's work, confirm the current branch, its merge base with `main`, and the working-tree state.
