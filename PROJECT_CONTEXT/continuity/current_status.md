# Current Status

## PROJECT_CONTEXT Layout

- The canonical memory index is `PROJECT_CONTEXT/context_index.yaml`.
- Task routing, records, and the dated ledger are grouped under
  `PROJECT_CONTEXT/tasks/`; knowledge is split under `PROJECT_CONTEXT/knowledge/`.
- Root registry YAML compatibility projections were retired on 2026-07-19.
  Historical task ledgers and reports retain their original path references.

## Workspace State

- Source root: `workspace_manifest.yaml -> workspace.source_of_truth`
- Codex loading root: `workspace_manifest.yaml -> platform_roots.codex`
- Claude Code project loading root: `workspace_manifest.yaml -> platform_roots.claude`
- OpenCode loading root: `workspace_manifest.yaml -> platform_roots.opencode`
- Hermes loading root: `workspace_manifest.yaml -> platform_roots.hermes`
- Skill projection links: `workspace_manifest.yaml -> projections[]`
- Raw external skill research root: `workspace_manifest.yaml -> external_roots.raw_skills`
- Curated adapted external skill root: `workspace_manifest.yaml -> external_roots.adapted_skills`
- Core skills:
  - `skills/disk-scan-reporter`
  - `skills/windows-ai-storage-governor`
  - `packages/character-system/engineering/generation/character-generator`
  - `packages/character-system/engineering/maintenance/character-maintainer`
  - `packages/character-system/engineering/diagnosis/style-doctor`
  - `packages/character-system/runtime/characters/zyc`
- Curated external skills currently exposed to Codex and Claude Code:
  `grill-me`, `grilling`, `handoff`, `diagnosing-bugs`, `tdd`, `code-review`,
  `codebase-design`, and `writing-great-skills`.
- Known external project roots are tracked separately in
  `PROJECT_CONTEXT/references/external_projects.yaml`; they are not workspace packages or
  skill projections.
- Registered external project: `math-modeling` at
  `${WORKSPACE_ROOT}/projects/数学建模`, private remote
  `git@github.com:AnieerLhayK/math-modeling.git`.
- Claude Code local launcher alias `math-modeling` maps to
  `${WORKSPACE_ROOT}/projects/数学建模` in the machine-local Claude project registry.
- Skill contracts now separate `role`, `authority`, `execution_modes`, and `exposures[]`.
- `platform` and `projection_path` remain temporary compatibility aliases for the first declared exposure.
- Related character skills are grouped by lifecycle role under
  `packages/character-system/`; unrelated future skills use `skills/`.
- Standalone governance skills live under `skills/`: `disk-scan-reporter`
  provides bounded read-only disk inventory and `windows-ai-storage-governor`
  provides storage governance. Their sources remain separate from platform
  projections.
- Claude Code and OpenCode conversation stores remain under
  `workspace_manifest.yaml -> session_stores`; source moves are tracked in
  `PROJECT_CONTEXT/continuity/session_migrations.json`.
- Health uses the governed CI classifier: core test failures block health;
  infrastructure-dependent failures remain visible in test details but do not
  downgrade the global result. Hermes guard script changes invalidate only the
  three matching allowlist approvals and require explicit managed reapproval.

## Completed Governance Work

- Git baseline established. Baseline commit in `reports/git_governance_report.md`: `64f31ecf4c414182d07802829fcca847bc93c302`.
- Report drift governance established.
- Runtime loop durable record structure established under `packages/character-system/reports/runtime-loop/`.
- Shared protocol validation layer established with `packages/character-system/shared/protocol_manifest.json`, schemas, and `scripts/validate_protocols.py`.
- Platform-named source directories were retired in favor of runtime and
  engineering package layers; Codex/OpenCode remain projection surfaces only.
- Character-package migration conversation continuity is protected by external
  Claude/OpenCode backups and `workspace sessions audit`.
- The character package now owns its domain protocols and runtime-loop records;
  root `shared/` contains workspace-global governance only.
- Task routing layer established with `PROJECT_CONTEXT/tasks/registry/index.yaml` to reduce broad context loading before maintenance work.
- Context budget layer established with `PROJECT_CONTEXT/governance/context_budget.md` to control expansion beyond required task context.
- Task ledger is partitioned under `PROJECT_CONTEXT/tasks/ledger/YYYY/MM.md` to preserve maintenance decisions without rereading broad context.
- Task outcomes have a separate tracked fact layer under `PROJECT_CONTEXT/tasks/records/`; `workspace records` validates and summarizes success, validation, edits, duration, token fields, and usability.
- Prompt registry established with `USAGE_GUIDES/prompt_registry.yaml` to resolve reusable prompt ids before regenerating meta-prompts.
- Task/prompt resolver established with `scripts/resolve_task_context.py`; it emits a bounded task view and avoids rereading full routing registries by default.
- Scripts governance migration established responsibility packages under
  `scripts/workspace/`, `scripts/validation/`, `scripts/publishing/`,
  `scripts/platform/`, and `scripts/reporting/`, with shared runtime helpers,
  mirrored domain tests, and long-lived root compatibility adapters. Legacy
  Python, PowerShell, VBS, JS, and import entry points remain supported.
- Context token meter established with per-task overrides, optional `tiktoken` support, a dependency-free heuristic fallback, and warning-first enforcement.
- P5.3 startup compression keeps root `AGENTS.md` below a machine-readable token ceiling and tests narrow-task budgets plus duplicate preloaded-file counting.
- Source-of-truth de-duplication pass established: current local path facts should live in `workspace_manifest.yaml`; docs should reference manifest fields or use placeholders.
- Platform exposure is no longer treated as skill ownership. One source skill may have multiple projections while retaining one role and authority contract.
- Agent governance now separates consumption from modification: Codex and
  Claude Code are default structural maintainers; Hermes and OpenCode are
  bounded record producers; unregistered agents are read/invoke/proposal-only.
- `workspace agent` can classify a path, explain a denied write, create a
  reviewable request, and validate an external temporary lease.
- Agent identity and lifecycle now use `shared/agent_registry.yaml`; role,
  capability, surface, and lease rules remain in `shared/agent_governance.yaml`.
- Codex and Claude Code are active structural maintainers. Hermes, OpenCode,
  and Reasonix are active validated record producers. Cursor remains a proposed
  Agent host and resolves to Consumer pending a tested runtime adapter.
- `workspace agent list/show/validate/doctor` provides the developer interface
  without automating activation, platform registration, or lifecycle mutation.
- `workspace changes verify <task-id>` compares unstaged, staged, and untracked
  Git paths with resolved task `write_scope`, marks high-risk paths, and
  preserves all out-of-scope work for human disposition.
- External workspace-task deliverables now resolve through
  `workspace_manifest.yaml -> output_roots.workspace`; repository-native
  artifacts and transient staging remain separate classes.
- Character-system exposure follows lifecycle needs: generator and maintainer
  are available to Codex and Claude Code; runtime character and style doctor
  are declared for Codex, Claude Code, OpenCode, and Hermes.
- OpenCode `style-doctor` and `zyc` loading entries are source-linked junctions to their workspace directories; the replaced identical directory copies are preserved under `${DATA_ROOT}/opencode\projection-backups\20260611-232730`.
- Manifest portability and bootstrap discovery checks are present in the current workspace:
  - `scripts/bootstrap_workspace.py`
  - `scripts/validate_manifest.py`
  - `scripts/migration_dry_run.py`
  - `shared/manifest_portability_policy.md`
- The single-agent developer CLI roadmap is complete:
  - bounded task and prompt routing;
  - context-budget preflight;
  - change-surface planning;
  - knowledge lookup;
  - report freshness checks;
  - failure diagnostics;
  - live health and governance summaries;
  - the user-level `workspace` launcher.
- `CLAUDE.md` imports root `AGENTS.md`, so Claude Code and agents that read
  `AGENTS.md` share one tracked startup policy instead of maintaining copies.
- Tracked `.claude/` rules and a PreToolUse guard identify this repository as a
  governed skill workspace and block writes to external or unregistered layers.
- The Claude boundary guard detects PowerShell-wrapped external writes and
  tells users to restart Claude from the target Git root instead of bypassing
  blocked native editing tools.
- The CNN implementation is maintained in a separate Git repository and is
  selected through the machine-local `claude-project cnn` launcher alias.
- `workspace_manifest.yaml` does not register external Claude projects; it
  remains the registry for workspace skills, protocols, and platform exposure.
- PROJECT_CONTEXT disassembly completed:
  - `architecture.md` + `workspace_purpose.md` merged into root `ARCHITECTURE.md`.
  - `coding_style.md` merged into
    `WORKSPACE_ENGINEERING/skill_engineering/style_alignment.md`.
  - `protocols.md` moved to `shared/INDEX.md`.
  - `bugs.md` and `experiment_log.md` deleted (superseded by runtime loop).
  - `PROJECT_CONTEXT/` narrowed to active task memory only (task ledger, registry, status, todo, session handoff).
- Project-memory maintenance now has a dedicated low-cost task route instead of
  borrowing authority from governance-summary or task-registry tooling.
- `SKILL_ENGINEERING/` has been promoted to `WORKSPACE_ENGINEERING/`.
  Workspace architecture, governance, portability, provenance, and case studies
  now form the parent knowledge layer; Skill Engineering remains a dedicated
  subdomain.
- External engineering sources now require attribution, license/usage notes,
  applicability limits, and a separate local-validation status before their
  lessons can be promoted.
- The Agent Registration Contract is the first validated Workspace Engineering
  case study, and the Claude write boundary recognizes the promoted directory.
- Change-risk classification now reuses Agent Governance surface classes and
  one machine-readable risk policy. The verifier reports normal, elevated, or
  high risk without treating declared high-risk maintenance as forbidden.
- `workspace workflow check <task-id>` provides a read-only daily maintenance
  checkpoint: task resolution, scope verification, staged and unstaged
  whitespace checks, and routed validation guidance.
- Governance reduction is in a 5-to-10-task observation window. Ordinary PASS
  results create no extra report; only meaningful anomalies enter durable
  project memory.
- A confirmed Hermes incident showed that registration and Skill prose were
  not connected to runtime file tools. The unauthorized ZYC patch is preserved
  on `codex/safety-hermes-zyc-age-anchor-20260621` for later diagnosis and
  handoff.
- Runtime authorization now intersects Agent and acting-Skill authority.
  Hermes uses a tracked pre-tool guard, compact per-turn governance context,
  read-only terminal allowlisting, action-aware MCP checks, and filesystem MCP
  mutation exclusions.
- Workspace health now fails when the Hermes guard, hook consent, MCP
  restrictions, matcher coverage, approval timestamp, or agent-created Skill
  guard drift out of configuration.
- The character-system package migration preserved runtime-loop source but
  removed Hermes' ability to read package-shared templates through `skill_view`.
  Hermes now receives read-only filesystem access to the canonical package
  `shared/` and `reports/runtime-loop/` roots; mutation tools remain excluded.
- Hermes governance is workspace-scoped. External project work receives no
  workspace authority prompt or blanket terminal restriction unless a
  workspace Skill is active or the command targets a workspace/projection path.
- OpenCode now loads a project governance plugin and deny-first project
  permissions. The plugin binds mutating tool calls to Agent and acting-Skill
  authorization before files change, including MCP mutations.
- Reasonix now loads a project-local record-producer contract, explicit
  source/Git/MCP denials, bounded filesystem roots, and the shared
  style-doctor-to-handoff route. Its project configuration is active only when
  Reasonix runs from this workspace.
- Workspace health now checks Hermes, OpenCode, and Reasonix runtime adapters
  together and fails if Cursor is accidentally promoted beyond proposed
  Consumer authority.
- `workspace agent approve-hermes-guard` now previews the exact configured
  Hermes workspace hooks by default and requires `--approve --record-id` with
  an active external-write record to refresh their current script-mtime
  approvals. It retains unrelated allowlist entries.

## Context Efficiency Evidence

- Exact `o200k_base` measurements confirm that bounded routing reduces initial
  workspace context for ordinary maintenance:
  - `project_memory_maintenance`: 2,914 tokens;
  - `governance_summary_tooling`: 5,856 tokens;
  - `knowledge_interface_tooling`: 7,114 tokens.
- Registry-owning maintenance remains expensive:
  - `task_registry_update`: 28,353 tokens;
  - `context_resolution_tooling`: 38,678 tokens.
- The current conclusion is to keep narrow routes as the default and record
  only meaningful outliers. Do not optimize registry-owning routes merely to
  lower a number; revisit them when their cost blocks practical work.

## Recent Validation Results

- Hermes runtime-loop exposure validation: the filesystem MCP listed both
  canonical read roots and successfully read the diagnosis template while
  keeping four mutation tools excluded.
- The isolated workspace script suite passes 311 tests; the package-local
  qq-filter suite passes 23 and the disk-scan-reporter suite passes 35.
- A root-level pytest collection still has the four known baseline import
  errors: two qq-filter tests need the package import environment and two
  disk-scan tests use legacy `scripts.*` imports. No new collection failure was
  introduced by this documentation pass.
- The latest live check is `NEEDS_ATTENTION` only because Hermes runtime
  governance is not fully enforced. The workspace script-test health check
  passes when run with an isolated test runtime. This is a tracked runtime
  issue, not a README claim to hide.
- Manifest and protocol validation report 0 errors, with the known portability
  and lightweight-schema warnings. All three current report groups are fresh.
- Link and registered Markdown companion checks pass. Existing Chinese
  companions are synchronized when present; missing companions are not
  created automatically.
- Link and registered Markdown companion checks currently pass. Existing
  Chinese companions are synchronized when present; missing companions are not
  created automatically.
- The read-only `workspace sessions audit` still reports the pre-existing
  OpenCode/qq-raw-filter continuity failures; this migration does not touch
  external session stores or backups.
- README governance uses the manifest, shared policy, publisher configuration,
  and live checks as facts. Root and section README files provide navigation
  and local contracts rather than parallel path registries.
- `scripts/check_links.ps1`: validate all manifest projections and shared
  uniqueness after each exposure change.

## External Knowledge / RAG Planning

A bounded planning evaluation of whether future external RAG / knowledge base
would improve workspace maintenance is recorded under
`WORKSPACE_ENGINEERING/external_knowledge/external_rag_planning.md`.

- **Current phase:** P0 in progress. `use_when_zh` summaries are present for
  all current task ids; Chinese alias audit and natural-language task fallback
  remain open. No retrieval implementation exists.
- **Decision rule:** complete P0, observe 5–10 tasks, then decide whether
  P2–P5 (directory, BM25, CLI) are justified.
- **Boundary:** No external directories, indexes, databases, vector stores,
  or retrieval services will be created until P0 effectiveness is measured.
- `knowledge/index.yaml` has a new `external_knowledge_planning` topic.

## Current Unfinished Or Open Work

- The developer CLI is in an observation period. New commands should be added
  only after repeated real tasks demonstrate a missing interface.
- Runtime loop records exist structurally, but real diagnosis/handoff/patch/validation instances still need to be created during future drift events.
- Prompt registry entries are lightweight; future prompt-heavy work can split long prompt bodies into dedicated template files if needed.
- Runtime loop ledger updates are still manual.
- Protocol schemas are lightweight and not yet used for deep packet instance validation.
- Manifest still centralizes local absolute platform deployment paths.
- Legacy single-platform skill fields remain during the compatibility period and should not be removed until all consumers read `exposures[]`.
- CRLF warnings are still not governed by `.gitattributes`.
- Migration session backups are intentionally retained under `${DATA_ROOT}`;
  cleanup requires explicit user approval after the new layout has been used.
- Retired legacy projection roots may still appear in old reports or prompts. Treat `workspace_manifest.yaml` as current truth before acting on any historical path.
- Cross-agent work is supported through Git branches and tracked project context,
  but each agent must verify its branch is based on current `main` before editing.
- The next unrelated skill should begin under `skills/<skill-id>/`; package
  promotion remains conditional on demonstrated domain sharing.
- External business projects must not be created as new workspace top-level
  directories. `workspace health` treats a root `claude/` project directory as
  a boundary failure.
- Raw external skill snapshots are kept under the resolved
  `workspace_manifest.yaml -> external_roots.raw_skills` path and are not
  workspace source or platform projections. Adapted candidates are
  tracked under `external-skills/<function>/` only after the compatibility queue
  records provenance, applicability, adaptation, validation, and registration.
- Every newly discovered raw skill must be added to
  `PROJECT_CONTEXT/todo/external-skills.md` before evaluation, so research
  sources cannot silently disappear from the future-work queue.

## Important Caution

Do not assume the currently checked-out branch is `main`. Before continuing
another agent's work, inspect `git status --short --branch`,
`git log main..HEAD --oneline`, and the merge base with `main`.
