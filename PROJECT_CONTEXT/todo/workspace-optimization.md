# Workspace Optimization

This file contains workspace-native follow-up work. External skill intake is
tracked separately in `external-skills.md`.

## P1: Active Observation

- Continue using the completed developer CLI on real maintenance tasks.
- Record a context-budget observation only when a route exceeds its warning
  threshold, loads an unnecessary layer, or lacks authority for the intended
  maintenance surface.
- Treat the current measured baseline as evidence that narrow routing works:
  ordinary knowledge, governance, and project-memory routes resolve below the
  10,000-token warning threshold.
- Investigate registry-owning routes only when their high initial context causes
  practical friction; they currently exceed the warning threshold because they
  must load the registries and resolver implementation they maintain.
- Use `skills/<skill-id>/` for the next unrelated native skill. Promote it to a
  package only after real domain sharing appears.
- Run one bounded Cursor experiment before changing its proposed registration.
  Confirm caller identity, session boundary, cache location, and whether the
  client can honor an exact `reports/agent-experiments/cursor/` scope.

## P1: Prompt Library Module Follow-Ups

- Keep `USAGE_GUIDES/PROMPT_LIBRARY.md` as the user-facing entry point.
- Keep `USAGE_GUIDES/prompt_registry.yaml` as the machine-readable prompt id
  index, and full prompt bodies under `USAGE_GUIDES/PROMPT_TEMPLATES/`.
- Add report-refresh, skill-release, platform-exposure, and model-routing
  prompt families only where repeated work justifies them.
- Add lightweight validation for missing template paths and duplicate prompt ids
  if registry growth makes manual review brittle.
- Do not make the prompt library a permission system.

## P1: Governance Observation Window

- Observe the risk verifier and daily workflow across 5 to 10 real maintenance
  tasks before removing or expanding governance mechanisms.
- Record only meaningful anomalies: false positives, overly broad or narrow
  write scopes, unused registry fields, lease/worktree friction, policy blocks,
  prevented scope violations, or real pollution events.
- Exercise the Hermes guard across 5 to 10 real QQ/WeChat tasks and the OpenCode
  and Reasonix project guards on real diagnosis/handoff tasks.
- Review safety branch `codex/safety-hermes-zyc-age-anchor-20260621` through
  character-maintainer before deciding whether the preserved age-anchor patch
  should be accepted, revised, or rejected.

## P1: Triggered By Real Events

- When the next runtime drift occurs, create diagnosis, handoff, patch,
  validation, and optional generalization records from existing templates.
- After several runtime-loop cases exist, evaluate automation for IDs, ledger
  row insertion, and cross-link validation.
- Deepen protocol validation only after real packets expose validation needs.
- Build a ZYC evolution case library only from validated runtime lessons.
- Split a prompt registry entry into a dedicated template only when its prompt
  frame becomes too large for low-cost routing.

## P2: Deferred Enhancements

- Add `.gitattributes` or a CRLF policy pass if line-ending warnings keep
  creating noise.
- Archive or document `.git.disabled-*` projection metadata outside runtime
  projection roots.
- Consider deriving projection paths from `platform_roots` in a future manifest
  format.
- Add stale-report detection for manifest validation and migration reports.
- Extend package validation only when a second real package exposes missing
  generalization in the current contract.
- Retire legacy `skills[].platform` and `skills[].projection_path` only after
  all local and external consumers read `exposures[]`.
- Consider reviewed activate/suspend/retire helpers only after manual registry
  changes become repetitive; do not automate external installation or cleanup.
- Consider a public documentation export only after several
  `WORKSPACE_ENGINEERING/` case studies pass privacy, portability, attribution,
  and editorial review.

## P1: Claude Notification Fix Follow-Up

- Install the merged UTF-8-safe Claude long-task notification hooks into the
  managed user hook location using the workspace installer.
- Run the Windows PowerShell health test and a real smoke test from a project
  path containing Chinese characters.
- Confirm the temporary UTF-8 message-file path is cleaned up and that Hermes
  notification delivery remains non-blocking before treating this follow-up as
  complete.

## P2: External Knowledge / RAG Evaluation

- Complete the remaining P0 items of the external knowledge planning roadmap:
  audit Chinese aliases in `knowledge_registry.yaml` and add natural-language
  task-suggest fallback to `AGENTS.md`.
- After 5 to 10 real maintenance tasks using those improvements, revisit
  `WORKSPACE_ENGINEERING/external_knowledge/external_rag_planning.md`.
- Do not create external indexes, databases, vector stores, or retrieval
  services until P0 effectiveness is measured.
