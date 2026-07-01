# Workspace Agent Instructions

@AGENTS.md

@shared/claude/policies/model-routing-policy.md

## Claude Code

- Use the workspace task resolver and CLI exactly as described in `AGENTS.md`.
- Treat model-routing guidance as a visible recommendation only; it must never
  edit model configuration, provider settings, plugins, or permission policy.
- Apply model-routing guidance only when `.claude/model-routing-advice.json`
  has `"enabled": true`. If it is set to `false`, do not output model-tier
  assessments and behave as if this model advice integration is absent.
- Re-run the model complexity assessment for every new user task/request in
  this session, including low-risk requests; do not limit it to the first turn.
- Output that assessment before any tool call, file read, search, Todo,
  planning step, or subagent/Agent delegation. Internal policy reads or
  delegated exploration prompts do not count as the visible assessment.
- If the assessment is `Recommend Pro`, pause before tools or substantive work
  until the user switches models, says they already switched, or explicitly
  chooses to continue with the current model / ignore the recommendation.
- If the assessment is `Flash sufficient`, continue normally after the one-line
  assessment.
- Do not downgrade high-risk guard, permission, Git conflict, security,
  stability, or cross-system diagnosis work merely because the user asks for
  read-only planning or says not to modify files first.
- Requests about workspace guard or write-permission differences across Claude
  Code, Codex, OpenCode, and Hermes are Pro-class governance design tasks.
- Workspace health plus workflow out-of-scope diagnosis, stale report diagnosis,
  Git merge conflicts, and long-lived branch conflict planning are also
  Pro-class even when the first step is read-only.
- Treat `.claude/project-boundary.json` and `.claude/rules/` as the Claude-specific workspace boundary.
- This workspace is not the CNN project. Use `claude-project cnn` before any CNN work.
- This workspace is not the ztemp project. Use `claude-project ztemp` before any ztemp work.
- Direct `claude` startup from the target repository root is supported; do not
  switch repositories inside an already-running Claude session.
- If a boundary hook blocks native editing, restart in the correct repository
  instead of bypassing it with shell-based file rewriting.
- Treat Claude auto memory as local convenience only; durable decisions belong in the tracked workspace sources.
- Before continuing another agent's work, confirm the current branch, its merge base with `main`, and the working-tree state.
