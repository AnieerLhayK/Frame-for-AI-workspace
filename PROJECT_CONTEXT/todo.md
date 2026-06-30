# Todo

This file tracks unfinished or condition-triggered work. Always-on operating
rules belong in `AGENTS.md`, `PROJECT_CONTEXT/context_budget.md`, and shared
policies rather than being repeated as tasks here.

## P1: Active Observation

- Continue using the completed developer CLI on real maintenance tasks.
- Record a context-budget observation only when a route exceeds its warning
  threshold, loads an unnecessary layer, or lacks authority for the intended
  maintenance surface.
- Treat the current measured baseline as evidence that narrow routing works:
  ordinary knowledge, governance, and project-memory routes resolve below the
  8,000-token warning threshold.
- Investigate registry-owning routes only when their high initial context causes
  practical friction; they currently exceed the warning threshold because they
  must load the registries and resolver implementation they maintain.
- Use `skills/<skill-id>/` for the next unrelated skill. Promote it to a package
  only after real domain sharing appears.
- Run one bounded Cursor experiment before changing its proposed registration.
  Confirm caller identity, Session boundary, cache location, and whether the
  client can honor an exact `reports/agent-experiments/cursor/` scope.

## P1: Prompt Library Module Follow-Ups

- The foundation branch `codex/prompt-library-foundation` has been merged back
  to `main`; use focused short-lived branches for future prompt families unless
  a larger rebuild explicitly needs a long-running branch.
- Treat `USAGE_GUIDES/PROMPT_LIBRARY.md` as the user-facing entry point for the
  prompt library module.
- Keep `USAGE_GUIDES/prompt_registry.yaml` as the machine-readable prompt id
  index, and keep full copy-ready prompt bodies under
  `USAGE_GUIDES/PROMPT_TEMPLATES/`.
- Build the library in small phases:
  1. done: add first workspace-maintenance templates for health remediation,
     scoped change planning, task handoff continuation, and branch merge review;
  2. next: add report-refresh, skill-release, platform-exposure, and
     model-routing prompt families only where repeated work justifies them;
  3. next: add lightweight validation for missing template paths and duplicate
     prompt ids if registry growth makes manual review brittle;
  4. later: add search only after enough entries exist to justify it.
- Do not make the prompt library a permission system. Prompt reuse must not
  bypass task routing, write scope, model-routing boundaries, or Git checks.

## P1: Workspace Structure Optimization Follow-Ups

- Treat ignored `external-skills/` content as external tool/source drops, not
  workspace maintenance input. Do not inspect or clean it unless a task
  explicitly names that path or uses that external skill as a tool.
- Treat `.agents/` as an empty runtime-reserved directory for now. Add a tracked
  README only if an agent-state workflow starts using it as source context.
- Treat ignored `mcp/servers/`, `mcp/downloads/`, and `mcp/logs/` content as
  local MCP payload/runtime state. Do not inspect or clean it during ordinary
  workspace optimization; deletion remains explicit cleanup work.
- Revisit character reference sharing only after at least two runtime
  characters show the same reference structure and maintenance pain.

## Governance Observation Window

- Observe the risk verifier and daily workflow across 5 to 10 real maintenance
  tasks before removing or expanding governance mechanisms.
- Record only meaningful anomalies: verifier false positives, write scopes that
  are too broad or narrow, unused Registry fields, lease or worktree friction,
  a reasonable task blocked by policy, a prevented scope violation, or a real
  pollution event the rules failed to catch.
- Do not create an extra report for an ordinary PASS. Use Git history, a short
  Task Ledger entry for material decisions, and diagnosis or handoff records
  only for real incidents.
- After the observation window, consider removing unused Registry fields,
  merging duplicate guidance, simplifying lease interaction, reducing
  unnecessary worktree recommendations, and deleting classifications that
  never affect a decision.
- Do not remove a field or rule merely because one task did not use it.
- Exercise the Hermes guard across 5 to 10 real QQ/WeChat tasks. Record only
  false blocks, bypasses, missing tool coverage, or successful prevention.
- Exercise the OpenCode and Reasonix project guards on real diagnosis/handoff
  tasks. Record only bypasses, false blocks, missing target extraction, or
  successful prevention; ordinary PASS runs need no report.
- Review safety branch `codex/safety-hermes-zyc-age-anchor-20260621` through
  character-maintainer before deciding whether the preserved age-anchor patch
  should be accepted, revised, or rejected. Diagnosis and handoff are preserved
  on commit `deaee4c`.

## P1: Triggered By Real Events

- When the next runtime drift occurs, create real diagnosis, handoff, patch,
  validation, and optional generalization records from the existing templates.
- After several real runtime-loop cases exist, evaluate automation for runtime
  loop IDs, ledger row insertion, and cross-link validation.
- Deepen protocol validation for runtime packet instances only after real
  packets expose validation needs.
- Build a ZYC evolution case library only from validated runtime lessons.
- Split a prompt registry entry into a dedicated template only when its prompt
  frame becomes too large for low-cost routing.
- When the first externally sourced engineering lesson is added, exercise the
  provenance intake fields and verify that attribution, license notes, local
  validation, and applicability limits are sufficient for public sharing.

## P2: Deferred Enhancements

- Add `.gitattributes` or a CRLF policy pass if line-ending warnings keep
  creating noise.
- Archive or document `.git.disabled-*` projection metadata outside runtime
  projection roots.
- Consider deriving projection paths from `platform_roots` in a future manifest
  format.
- Add stale-report detection for manifest validation and migration dry-run
  reports.
- Extend package validation only when a second real package exposes missing
  generalization in the current contract.
- Retire legacy `skills[].platform` and `skills[].projection_path` only after
  all local and external consumers have migrated to `exposures[]`.
- Consider reviewed activate/suspend/retire helpers only after manual registry
  changes become repetitive; do not automate external installation or cleanup.
- Consider a public documentation export only after several
  `WORKSPACE_ENGINEERING/` case studies have passed privacy, path portability,
  attribution, and editorial review.

## P2: External Knowledge / RAG Evaluation

- Complete the remaining P0 items of the external knowledge planning roadmap:
  1. Audit Chinese aliases in `knowledge_registry.yaml`.
  2. Add natural-language task-suggest fallback to `AGENTS.md`.
- Done for P0: `use_when_zh` summaries have been added for all current
  task-ids in `task_registry.yaml`.
- After 5–10 real maintenance tasks using P0 improvements, revisit
  `WORKSPACE_ENGINEERING/external_knowledge/external_rag_planning.md`
  to decide whether P2–P5 (directory structure, BM25 prototype, CLI)
  are justified.
- If wrong-task-id rate drops after P0, defer P2–P5 indefinitely.
- Do not create external directories, index files, databases, or
  vector stores until P0 effectiveness is measured.
