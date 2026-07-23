# Potential For Future

This directory stores durable but non-active planning material that should be
remembered without becoming an immediate todo item or enforceable policy.

## Categories

- `optimization_options.yaml`: active candidate or in-progress workspace,
  architecture, tooling, or workflow improvements.
- `risk_register.yaml`: active candidate or observed structural, exposure, and
  migration risks.
- `history/`: tracked terminal decisions, split by the same two registry types.
  It is durable project memory, not an ignored backup or ordinary startup context.

Entries are retrieval aids, not implementation plans. Promote an entry to task
routing, policy, active todo, or source code only after current evidence and
scope are confirmed.

Move implemented/rejected options and mitigated/accepted/retired risks into the
matching history registry. Preserve the original entry and add `archived_at`
plus `source_registry`; `scripts/validate_future_register.py` enforces this
boundary.

When adding a category, update this README, its Chinese companion, the
`PROJECT_CONTEXT/knowledge/index.yaml` entry, and any task-routing rules
that need to discover it. Historical task ledgers are not rewritten merely
because a registry moved.
