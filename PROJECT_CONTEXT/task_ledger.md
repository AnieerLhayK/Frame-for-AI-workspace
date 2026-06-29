# Task Ledger

This ledger records workspace maintenance tasks that future sessions should remember without rereading broad context.

It is a continuity layer, not a stronger source of truth than `workspace_manifest.yaml`, `shared/`, or current Git state.

## Read Policy

For normal maintenance, read only the latest 5 entries.

Read older entries only when:

- the user asks for historical reconstruction;
- a current conflict refers to an older decision;
- a migration, cleanup, or platform exposure task needs the older path history.

## Write Policy

Append an entry when a task changes or materially confirms one of these:

- task routing, context budget, or prompt routing;
- platform exposure paths or loading surfaces;
- source-of-truth boundaries;
- shared protocols, runtime loop rules, or validation behavior;
- cleanup, migration, archival, or deletion decisions;
- generated reports or validation snapshots.

Do not add entries for every command, read, or tiny edit. The entry should capture decisions and next actions.

## Entry Format

```text
### TASK-YYYYMMDD-NNN - Short title

- Date:
- Status:
- Task type:
- Branch:
- Commit:
- Read:
- Modified:
- Decision:
- Validation:
- Next:
```

## Recent Entries

### TASK-20260629-002 - Fix public CI validate-links test gating

- Date: 2026-06-29
- Status: implemented
- Task type: skill_release_packaging
- Branch: main
- Commit: pending
- Read:
  - GitHub Actions failure log for `Frame-for-AI-workspace` run 28374155583
  - scripts/ci_run.py
  - scripts/tests/test_workspace_cli.py
  - scripts/publish_public.py and publish staging output
- Modified:
  - `scripts/workspace_cli.py` now resolves PowerShell as `powershell.exe`,
    then `pwsh`, then a final `powershell.exe` fallback for `validate links`
    and workspace report refresh commands.
  - `scripts/tests/test_workspace_cli.py` now skips the live
    `workspace validate links` output integration assertion only when neither
    `powershell.exe` nor `pwsh` is available, and covers the `pwsh` fallback.
- Decision:
  - Keep the static no-`Format-Table` regression test as a cross-platform core
    test.
  - Treat the live PowerShell link-check rendering assertion as a
    PowerShell-capable environment test, and make the CLI use `pwsh` on
    non-Windows runners where that is the available PowerShell executable.
- Validation:
  - `python -m unittest scripts.tests.test_workspace_cli` passed.
  - `python -m unittest scripts.tests.test_publish_public` passed.
  - `python scripts/publish_public.py --out-dir ${DATA_ROOT}/codex\cache\staging\frame-ai-workspace-ci-fix --repo-name Frame-for-AI-workspace` passed.
  - `python scripts/publish_check.py --dir ${DATA_ROOT}/codex\cache\staging\frame-ai-workspace-ci-fix` passed.
  - `python ${DATA_ROOT}/codex\cache\staging\frame-ai-workspace-ci-fix\scripts\ci_run.py` returned PASS with 0 core failures and only expected infra-dependent failures.
  - `git diff --check` passed.
- Next:
  - Commit and sync `Frame-for-AI-workspace` remote again, then confirm the
    GitHub Actions `python-quality` run passes.

### TASK-20260629-001 - Add public workspace beginner setup and remote-only sync rule

- Date: 2026-06-29
- Status: implemented
- Task type: skill_release_packaging
- Branch: main
- Commit: pending
- Read:
  - scripts/publish_public.py
  - scripts/publish_check.py
  - scripts/sync_public_repo.py
  - WORKSPACE_ENGINEERING/PUBLISH.md
  - scripts/tests/test_publish_public.py
  - scripts/tests/test_workspace_cli.py
- Modified:
  - Public skeleton generation now emits `BEGINNER_GUIDE.md`.
  - Public skeleton generation now emits `scripts/setup_public_workspace.py`, a
    conservative first-run helper that renders template variables, creates a
    basic data root, and runs read-only checks for CLI help, task list,
    `workspace explain`, agent list, and health.
  - Public publish verification now requires the beginner guide and setup
    helper and exercises `workspace explain mechanism task-routing`.
  - `scripts/sync_public_repo.py` now treats local public checkouts as
    disposable staging, defaulting to `PUBLIC_STAGING_DIR`,
    `AI_TOOL_STAGING_DIR`, or a system temp staging root instead of a durable
    workspace-local deployment.
  - `WORKSPACE_ENGINEERING/PUBLISH.md` now states that
    `Frame-for-AI-workspace` is remote-only as the durable public repository.
- Decision:
  - Keep `Frame-for-AI-workspace` as a generated remote artifact; do not
    maintain a separate local deployment repository inside this workspace.
  - Make the new setup helper conservative: it prepares only the skeleton's own
    basic functions and leaves provider credentials, plugins, model settings,
    and platform projections as explicit manual steps.
- Validation:
  - `python -m unittest scripts.tests.test_publish_public` passed.
  - `python -m py_compile scripts/publish_public.py scripts/publish_check.py scripts/sync_public_repo.py` passed.
  - `python scripts/publish_public.py --out-dir ${DATA_ROOT}/codex\cache\staging\frame-ai-workspace-smoke --repo-name Frame-for-AI-workspace` passed.
  - `python scripts/publish_check.py --dir ${DATA_ROOT}/codex\cache\staging\frame-ai-workspace-smoke` passed.
  - `python ${DATA_ROOT}/codex\cache\staging\frame-ai-workspace-smoke\scripts\setup_public_workspace.py --workspace-root ${DATA_ROOT}/codex\cache\staging\frame-ai-workspace-smoke --data-root ${DATA_ROOT}/codex\cache\staging\frame-ai-workspace-smoke-data` completed core checks with expected optional health warning in the unconfigured skeleton.
  - `python -m unittest discover -s scripts/tests -p "test_*.py"` passed.
  - `python scripts/workspace_cli.py changes verify skill_release_packaging --agent codex --strict` passed.
  - `python scripts/workspace_cli.py workflow check skill_release_packaging` passed.
  - `git diff --check` passed.
- Next:
  - Commit the source changes, then run `python scripts/sync_public_repo.py --push`
    from a clean workspace to update the remote public repository.

### TASK-20260628-004 - Improve workspace CLI readability and explainability

- Date: 2026-06-28
- Status: implemented
- Task type: workspace_developer_experience, report_regeneration
- Branch: main
- Commit: ac1ca2b for phase 1; follow-up explain/link-output commit pending at entry time
- Read:
  - README.md and ARCHITECTURE.md
  - scripts/workspace_health.py and workspace health tests
  - scripts/workspace_cli.py and workspace CLI tests
  - scripts/resolve_task_context.py and resolver tests
  - scripts/workspace_explain.py and workspace explain tests
  - scripts/check_links.ps1 and scripts/setup_links.ps1
  - USAGE_GUIDES/QUICK_START/workspace_cli.md
  - report freshness tooling
- Modified:
  - Grouped `workspace health` text output into Core Workspace, Reports,
    Claude Code Boundary, Agent Runtime Guards, and Validation.
  - Added inline report-remediation guidance and an explanation for skipped
    tests.
  - Added Codex/Claude structural-maintainer checks to platform agent guard
    health.
  - Rendered `workspace task list` as grouped wrapped tables while preserving
    JSON output.
  - Expanded top-level `workspace --help` with common flows.
  - Updated the workspace CLI quick start to prefer `workspace ...` commands
    and include a Python command mapping table.
  - Added `workspace explain path/topic/mechanism` for read-only explanation
    of workspace paths, registered knowledge topics, and named mechanisms.
  - Changed link validation and setup output from truncating PowerShell tables
    to readable multiline records with full `LinkPath`, `ExpectedTarget`, and
    target fields.
  - Added `workspace_developer_experience` as the routed task for integrated
    human-facing CLI/health/task-list/explain/link-output/report-guide
    improvements.
  - Refreshed current report snapshots after source changes.
- Decision:
  - Keep the integrated `workspace` entry point as the primary developer
    surface and add bounded explanation commands inside it, instead of creating
    a separate black-box inventory system.
  - Keep health JSON flat for script compatibility; improve only the human text
    rendering.
  - Avoid table output for long console paths; use multiline records when path
    fields would otherwise be truncated.
- Validation:
  - `workspace reports refresh all-current` regenerated the current report
    snapshots.
  - `workspace reports status --strict` returned FRESH for all current report
    groups.
  - `workspace health --with-tests` returned PASS with grouped text output.
  - Focused tests for health, CLI, resolver, explain, and report freshness
    passed.
  - `python -m unittest discover -s scripts/tests -p "test_*.py"` passed.
  - `workspace task list`, `workspace --help`, `workspace explain path
    scripts/workspace_cli.py`, `workspace explain mechanism task-routing`, and
    `workspace validate links` were manually inspected for readable text output.
  - `workspace changes verify workspace_developer_experience --agent codex --strict`
    passed.
  - `workspace workflow check workspace_developer_experience` passed.
  - `git diff --check` passed.
- Next:
  - Consider a later ranking/filtering pass for `workspace explain path` if
    highly shared files produce too many related tasks.

### TASK-20260628-003 - Add lightweight Claude first-response model assessment

- Date: 2026-06-28
- Status: implemented
- Task type: claude_project_boundary
- Branch: main
- Commit: pending
- Read:
  - CLAUDE.md
  - shared/claude/policies/model-routing-policy.md
  - scripts/workspace_health.py and focused health tests
- Modified:
  - Replaced the single high-risk `Upgrade Message` with a two-tier
    `First Response Format`.
  - Low-risk work now has a one-sentence `Flash sufficient` assessment.
  - High-risk work now has a visible `Recommend Pro` quote block with a fixed
    permission boundary line.
  - Health checks and regression tests now guard the new first-response
    markers.
- Decision:
  - Keep model routing as advisory-only and do not introduce a scripted
    complexity scorer or any external model/provider configuration change.
- Validation:
  - `python -m unittest scripts.tests.test_workspace_health` passed.
  - `python -m unittest discover -s scripts/tests -p "test_*.py"` passed.
  - `git diff --check` passed.
  - `python scripts/workspace_cli.py changes verify claude_project_boundary --agent codex --strict`
    reported WARNING, not ERROR, due to the existing declarative
    machine-local launcher scope.
  - `python scripts/workspace_cli.py workflow check claude_project_boundary`
    reported WARNING with Git diff check PASS for the same declarative scope.
  - `workspace health --with-tests` reported `claude-model-routing`, Hermes,
    platform guards, and tests as PASS; overall health is NEEDS_ATTENTION
    because reports are stale after the policy source change.
- Next:
  - Optionally smoke test in a fresh Claude Code session with one low-risk and
    one high-risk prompt.

### TASK-20260628-002 - Refresh Hermes guard hook approval

- Date: 2026-06-28
- Status: completed
- Task type: runtime_authorization_enforcement, project_memory_maintenance
- Branch: main
- Commit: pending
- Read:
  - runtime authorization task context
  - Hermes config and shell hook allowlist
  - tracked `scripts/hermes_workspace_guard.py` mtime
  - agent governance policy, registry, and runtime enforcement adapters
- Modified:
  - Updated external
    `${DATA_ROOT}/hermes\shell-hooks-allowlist.json` for the three workspace
    guard hook approvals: `pre_tool_call`, `post_tool_call`, and
    `pre_llm_call`.
  - Set each workspace guard `script_mtime_at_approval` to the current tracked
    `scripts/hermes_workspace_guard.py` mtime.
  - No tracked source file was changed by the external allowlist update.
- Decision:
  - Treat the user request for remaining governance as explicit approval for
    this narrow environment-write operation.
  - Do not broaden Codex's registered capabilities to `environment_write`;
    this was a one-off local runtime approval refresh, not a policy expansion.
- Validation:
  - `workspace health --with-tests` returned PASS.
  - `workspace agent doctor hermes --format json` returned PASS.
  - `reports status --strict` returned FRESH for all current report groups.
- Next:
  - Reapprove the Hermes hook allowlist only when the tracked guard script
    changes again.

### TASK-20260628-001 - Retire stale model-routing governance branch

- Date: 2026-06-28
- Status: completed
- Task type: cleanup_migration, project_memory_maintenance
- Branch: main
- Commit: pending
- Read:
  - `git worktree list --porcelain`
  - `git log --left-right --cherry-pick --oneline main...codex/model-routing-governance`
  - `git diff d3d51ba..codex/model-routing-governance`
  - shared manifest portability and workspace path policies
- Modified:
  - Pruned the missing staging worktree metadata for
    `${DATA_ROOT}/codex\cache\staging\workspace-model-routing-governance`.
  - Deleted the local branch `codex/model-routing-governance`.
  - Recorded this cleanup decision in the task ledger.
- Decision:
  - The branch was based on `9bf94c1` and its staging worktree path no longer
    existed.
  - Its model-routing governance intent was superseded on `main` by
    `d3d51ba`, while `main` also retained later public publish/sync hardening
    and report refresh commits.
  - Do not merge or resurrect `44f57eb`; it would regress newer mainline
    governance and publish-tool changes.
- Validation:
  - `git branch -vv --all` shows only `main` and `origin/main`.
  - `git worktree list --porcelain` shows only `${WORKSPACE_ROOT}`.
- Next:
  - None for this branch.

### TASK-20260627-002 - Bound Claude model-routing recommendations

- Date: 2026-06-27
- Status: ported_to_main_worktree
- Task type: claude_project_boundary
- Branch: main
- Commit: pending
- Read:
  - CLAUDE.md
  - shared/claude/policies/model-routing-policy.md
  - .claude/project-boundary.json, .claude/rules/workspace-boundary.md,
    .claude/settings.json, and workspace boundary hook
  - scripts/workspace_health.py and focused health tests
  - prior handoff branch commit 44f57eb
- Modified:
  - CLAUDE.md states model-routing guidance is a visible recommendation only
    and must not edit model, provider, plugin, or permission settings.
  - shared/claude/policies/model-routing-policy.md has an explicit Authority
    Boundary section: model strength is not authority.
  - workspace health checks that the model-routing policy is loaded, visible,
    and non-authorizing.
  - claude_project_boundary task routing declares the shared Claude
    model-routing policy as required and writable context.
- Decision:
  - Port only the governance change from the isolated worktree instead of
    merging the stale branch over newer main publish/report fixes.
  - Keep model routing advisory: it may recommend `deepseek-v4-pro` before
    complex or high-risk work, but must not switch models, edit runtime
    configuration, or weaken workspace governance.
- Validation:
  - `python -m unittest scripts.tests.test_workspace_health` passed.
  - `python -m unittest discover -s scripts/tests -p "test_*.py"` passed.
  - `git diff --check` passed.
  - `workspace health --with-tests` reported the new `claude-model-routing`
    check and tests as PASS; overall health remains NEEDS_ATTENTION because
    reports are stale and Hermes guard approvals have pre-existing drift.
  - `workspace workflow check claude_project_boundary` reported WARNING, not
    ERROR, due to declarative machine-local launcher scope and the auto-updated
    `.claude/routing_events.ndjson` log.
- Next:
  - Verify in a real Claude Code session with a read-only complex-task prompt.
  - Do not expand this into a model router service unless explicitly approved.

### TASK-20260627-001 - Repair public workspace publishing scrub checks

- Date: 2026-06-27
- Status: completed
- Task type: skill_release_packaging, task_registry_update
- Branch: main
- Commit: pending
- Modified:
  - Tightened public workspace path scrubbing for JSON-escaped Windows paths.
  - Added `reasonix.toml` to public skeleton scrub coverage.
  - Added a publish-tool regression test for escaped path detection.
  - Expanded `skill_release_packaging` routing to include public skeleton
    publish, verify, and sync tooling.
- Decision:
  - Treat `scripts/publish_public.py`, `scripts/publish_check.py`, and
    `scripts/sync_public_repo.py` as release-packaging surfaces when they
    govern the public workspace skeleton.
- Validation:
  - Pending final commit validation.
- Next:
  - Sync the regenerated skeleton to `Frame-for-AI-workspace`.

### TASK-20260624-001 - Evaluate external RAG / knowledge base planning

- Date: 2026-06-24
- Status: planning_complete
- Task type: workspace_engineering_knowledge, knowledge_interface_tooling
- Branch: codex/workspace-rag-planning
- Branch commit: b4541b0 (planning baseline); P0 `use_when_zh` follow-up:
  3f751e6
- Read:
  - workspace architecture, task registry, context budget, change surface policy
  - knowledge_registry.yaml (20 topics, 66 entries)
  - WORKSPACE_ENGINEERING/README.md and book structure
  - PROJECT_CONTEXT/current_status.md, todo.md
  - existing ledger entries for routing and knowledge patterns
- Modified:
  - Created `WORKSPACE_ENGINEERING/external_knowledge/external_rag_planning.md`
    as bounded evaluation of external RAG/knowledge base feasibility.
  - Added `external_knowledge_planning` topic to knowledge_registry.yaml.
  - Added P2: External Knowledge / RAG Evaluation section to todo.md.
  - Added External Knowledge / RAG Planning section to current_status.md.
  - Added `external_knowledge/` subdirectory to WORKSPACE_ENGINEERING/README.md
    book structure.
  - This ledger entry.
- Decision:
  - Do not implement RAG now. Complete P0 first (Chinese alias audit,
    use_when_zh summaries, natural-language task-suggest fallback).
  - Observe 5–10 real maintenance tasks after P0, then decide whether P2–P5
    (directory structure, BM25 prototype, CLI) are justified.
  - If wrong-task-id rate drops after P0, defer P2–P5 indefinitely.
  - External retrieval lives under `${DATA_ROOT}\workspace-rag\`, never inside
    the workspace.
  - RAG is a suggestion layer, not a source of truth. Never derive policy,
    write targets, or validation from RAG output.
  - Governance rule: a new external retrieval mechanism must remove or
    simplify an existing mechanism, not stack on top of it.
- Validation:
  - Knowledge registry validation passed (21 topics, 67 entries).
  - Workspace health passed except pre-existing stale reports and Hermes
    guard items.
  - Changes limited to planning files. No scripts, indexes, databases, or
    vector stores created.
- Next:
  - P0.1: Audit knowledge_registry.yaml Chinese aliases for completeness.
  - P0.2: Add natural-language task-suggest fallback to AGENTS.md.
  - After P0: revisit the planning document after 5–10 real tasks.

- Date: 2026-06-23
- Status: draft_created
- Task type: skill_release_packaging
- Branch: main
- Commit: 6ec5843
- Modified:
  - Added a dedicated release-packaging task route.
  - Added deterministic ZYC Toolkit distribution source, private-access notes,
    beginner documentation, prompt cards, and guarded OpenCode installers.
  - Added a standalone text-only style-doctor product contract.
  - Added conditional standalone fallback notes to the maintained ZYC and
    style-doctor source documentation.
- Decision:
  - Keep the product release line independent under `zyc-toolkit/v0.1.0`.
  - Package ZYC from its maintained references instead of copying a second
    source tree.
  - Ship style-doctor without workspace ledgers, maintainer authority, or
    source-write behavior.
  - Publish to the current private repository as a draft and mark it non-Latest.
- Validation:
  - Both source skills passed lifecycle validation.
  - Release builds were byte-for-byte deterministic and passed content,
    checksum, UTF-8, frontmatter, forbidden-path, and privacy exclusions.
  - Junction, idempotent reinstall, copy fallback, conflict preservation,
    missing-CLI failure, and exact OpenCode discovery paths were verified in
    isolated configuration roots.
  - DeepSeek V4 Flash loaded the packaged ZYC and standalone style-doctor in
    separate sessions; neither session modified package files.
  - GitHub accepted both draft assets; the uploaded ZIP digest matched the
    locally generated SHA-256 exactly.
- Next:
  - Review the private Draft Release and its beginner instructions.
  - Publish the existing draft when the invited-user experience is accepted;
    do not recreate or retag the validated assets.

### TASK-20260622-003 - Extend runtime authority to OpenCode and Reasonix

- Date: 2026-06-22
- Status: completed
- Task type: runtime_authorization_enforcement
- Branch: main
- Commit: this commit
- Modified:
  - Added project-local deny-first governance for OpenCode and Reasonix.
  - Bound OpenCode mutating tools to shared Agent and acting-Skill checks.
  - Activated Reasonix as the same bounded record-producer class as Hermes and
    OpenCode.
  - Kept Cursor proposed and Consumer-only pending a tested adapter.
  - Added runtime adapter health checks and cross-platform regression tests.
- Decision:
  - Equivalent agents share one authority model; each platform gets the
    strongest project-local adapter it supports.
  - Project-local governance must not affect use of the tools in unrelated
    repositories.
  - Prompt guidance removes bargaining behavior, but tool boundaries remain the
    authority.
- Validation:
  - 218 workspace script tests passed.
  - Manifest validation passed with 0 errors and 0 warnings.
  - Protocol validation passed with 0 errors and the existing lightweight
    schema warning.
  - Runtime adapter health, strict scope verification, workflow check,
    Reasonix project loading, and OpenCode plugin/Skill loading passed.
- Next:
  - Observe real OpenCode and Reasonix diagnosis/handoff work for bypasses or
    false blocks. Leave Cursor unchanged until a bounded experiment is run.

### TASK-20260622-002 - Restore Hermes runtime-loop read exposure

- Date: 2026-06-22
- Status: completed
- Task type: runtime_authorization_enforcement
- Branch: codex/hermes-authority-cognition
- Commit: this commit
- Modified:
  - Hermes receives read-only access to character-system shared protocols,
    templates, and runtime-loop records at their canonical package paths.
  - The cognition hook forbids offering direct source patching as a shortcut.
  - Runtime enforcement applies only in workspace context, while active
    workspace Skills and explicit workspace targets remain guarded.
  - Health checks now detect missing runtime-loop read roots.
  - Workspace Engineering records the migration/read-dependency pattern.
- Decision:
  - The runtime-loop infrastructure was not lost in migration commit `059e4e2`;
    its platform read surface was lost.
  - Restore read access without copying shared source or reopening MCP write
    tools.
  - Treat user approval as task intent, never as an authority expansion.
  - Preserve the ZYC diagnosis and handoff with the unapproved patch on safety
    branch commit `deaee4c`.
- Validation:
  - Focused Hermes, health, and Agent governance suite passed: 66 tests.
  - Full workspace script suite passed: 207 tests.
  - Filesystem MCP listed both canonical runtime-loop read roots and read the
    diagnosis template successfully; four mutation tools remain excluded.
  - Direct hook evaluation returned no workspace context for external work and
    injected the strengthened authority contract after style-doctor activation.
  - Scope verification, workflow check, manifest, protocol, knowledge, hook
    doctor, and Git whitespace checks passed.
  - QQ and Weixin reconnected after runtime reload.
- Next:
  - Let character-maintainer review the safety branch in a separate task.

### TASK-20260622-001 - Fix cross-platform Hermes runtime path enforcement

- Date: 2026-06-22
- Status: done
- Task type: runtime_authorization_enforcement
- Branch: main
- Commit: pending
- Read:
  - failing GitHub Actions run `27902559786`
  - Hermes workspace guard, agent governance classifier, health check, and tests
- Modified:
  - host-independent workspace, projection, and external path classification
  - Hermes payload cwd/path resolution and runtime-record authorization
  - Hermes guard health path checks and POSIX-runner regression coverage
  - current manifest and protocol validation snapshots
- Decision:
  - Interpret paths using their declared Windows, UNC, or POSIX style instead of
    the runner operating system.
  - Route all guarded writes through the shared agent-governance classifier.
  - Continue allowing explicit external output while failing closed for
    unresolved or unauthorized workspace mutation.
- Validation:
  - Hermes/agent-governance/health focused tests passed (61).
  - Full workspace script tests passed (202).
  - Style-doctor diagnosis writes are allowed; ZYC diagnosis writes are denied.
  - Workspace health passes except for the expected stale local Hermes hook
    approval, which must be renewed after the final script commit.
- Next:
  - Push `main`, confirm Ubuntu CI, then renew the local Hermes hook approval.

### TASK-20260621-004 - Enforce Hermes runtime authority

- Date: 2026-06-21
- Status: completed
- Task type: runtime_authorization_enforcement
- Branch: codex/hermes-runtime-governance-enforcement
- Commit: this commit
- Modified:
  - Agent checks now intersect optional acting-Skill execution modes.
  - Scope and workflow verification accept `--agent` and `--skill`.
  - Hermes gains pre-tool blocking, compact per-turn governance context,
    active-Skill tracking, read-only terminal allowlisting, action-aware MCP
    checks, and guard health checks.
  - ZYC and style-doctor expose machine-readable related-Skill routes.
- Decision:
  - Memory and prompt guidance are cognitive aids, not authorization.
  - Hermes source writes fail before mutation even when task scope is broad.
  - Diagnosis and handoff records remain writable only when both Agent and
    acting Skill permit `record_write`.
  - The unauthorized age-anchor patch remains isolated on safety commit
    `ce6eddf` for later diagnosis; it is not accepted into main.
- Validation:
  - Focused governance suite passed: 112 tests.
  - Full workspace script suite passed: 200 tests.
  - Real Hermes hooks blocked source patch, process, unsafe terminal, and
    unresolved MCP mutation calls before execution.
  - ZYC source write returned DENY; style-doctor diagnosis write returned ALLOW.
  - Scope verification, workflow check, manifest, knowledge, protocol, report
    freshness, health, and Git whitespace checks passed.
  - QQ and Weixin gateways reconnected after the guarded runtime reload.
- Next:
  - Observe real messaging tasks and diagnose the preserved ZYC proposal.

### TASK-20260621-003 - Unify risk and simplify maintenance workflow

- Date: 2026-06-21
- Status: completed
- Task type: governance_workflow_simplification
- Branch: codex/governance-workflow-simplification
- Commit: this commit
- Modified:
  - unified machine-readable risk classification and scope-verifier output
  - read-only `workspace workflow check <task-id>` command and tests
  - concise workflow guidance and a 5-to-10-task governance observation window
- Decision:
  - Reuse Agent Governance surfaces instead of creating another permission model.
  - Keep high-risk paths editable when declared; require confirmation for
    destructive or externally visible operations.
  - Recommend worktrees only for isolation-worthy operations; keep temporary
    structural leases isolated by requirement.
  - Defer governance deletion until real tasks produce enough evidence.
- Validation:
  - Focused verifier, workflow, and CLI suite passed: 50 tests.
  - Full workspace script suite passed: 170 tests.
  - Scope verification and workflow check both returned PASS on the real change set.
  - Knowledge, manifest, protocol, report freshness, workspace health, and
    Git whitespace checks passed; protocol validation retained its established
    lightweight schema-depth warning.
- Next:
  - Observe meaningful anomalies across 5 to 10 real maintenance tasks.

### TASK-20260621-002 - Add post-change scope verification

- Date: 2026-06-21
- Status: completed
- Task type: change_scope_verification, developer_interface_tooling
- Branch: codex/change-scope-verification
- Commit: 0ee5655 (verifier and CLI); documentation/report commit follows
- Read:
  - change-surface policy, planner, resolver contract, CLI, tests, and Git workflow guidance
  - Workspace Engineering governance and boundary lessons
- Modified:
  - read-only Git change collector and task write-scope verifier
  - `workspace changes verify <task-id>` CLI integration
  - focused task route, tests, startup rule, CLI guidance, and governance methodology
- Decision:
  - Treat actual Git paths as evidence and resolved write scope as authority.
  - Mark declared high-risk work without forbidding capable maintainers.
  - Return errors for explicit scope violations while preserving every file.
  - Keep safety branches, worktree lifecycle, rollback, and change splitting manual.
- Validation:
  - Focused verifier, planner, CLI, and startup suite passed: 54 tests.
  - Full workspace script suite passed: 160 tests.
  - The verifier returned PASS on the real unstaged/untracked task changes.
  - Declared high-risk governance files were identified without blocking them.
  - Knowledge registry validation passed with 20 topics and 66 entries.
  - Manifest validation passed with 0 errors and 0 warnings.
  - Protocol validation passed with 0 errors and the established lightweight
    schema-depth warning.
  - Existing `workspace changes plan` behavior passed.
  - Root Agent startup instructions remained within the 900-token regression ceiling.
  - Git whitespace validation passed.
- Next:
  - Observe real tasks before considering any safety-branch or worktree automation.

### TASK-20260621-001 - Fix cross-platform agent governance validation

- Date: 2026-06-21
- Status: done
- Task type: agent_governance_update
- Branch: codex/workspace-engineering-knowledge
- Commit: pending
- Read:
  - failing GitHub Actions run `27869306856`
  - agent governance policy, registry, implementation, and tests
- Modified:
  - cross-platform absolute path detection in agent registration validation
  - agent governance regression tests
  - current manifest and protocol validation snapshots
- Decision:
  - Recognize Windows drive, UNC, and POSIX absolute paths independently of the
    runner operating system.
  - Preserve fail-closed degradation for genuinely invalid registrations.
- Validation:
  - Agent governance and workspace CLI tests passed (45).
  - Full workspace script tests passed (145), including an explicit POSIX
    workspace-root simulation with Windows external storage paths.
  - Agent role, scope, and Hermes write-boundary checks passed.
  - Manifest validation completed with 0 errors and 0 warnings.
  - Protocol validation completed with 0 errors and 1 known lightweight-schema
    warning.
- Next:
  - Push the branch and confirm GitHub Actions passes on Ubuntu.

### TASK-20260620-005 - Promote Skill Engineering to Workspace Engineering

- Date: 2026-06-20
- Status: completed
- Task type: workspace_engineering_knowledge, knowledge_interface_tooling, startup_context_optimization
- Branch: codex/workspace-engineering-knowledge
- Commit: pending
- Read:
  - existing Skill Engineering knowledge files and current knowledge routes
  - task/context routing, CLI layer filters, planner classification, and Claude boundary policy
  - the completed Agent Registration Contract and its validation evidence
- Modified:
  - promoted `SKILL_ENGINEERING/` to `WORKSPACE_ENGINEERING/`
  - retained Skill Engineering as a dedicated subdomain
  - added provenance, evidence-level, public-sharing, case-study, and template guidance
  - captured Agent Registration Contract as the first validated workspace case study
  - added a low-cost task route and canonical knowledge layer with legacy CLI alias
  - updated the Claude top-level write boundary
- Decision:
  - Treat reusable AI workspace engineering as the parent discipline.
  - Keep current state and enforceable policy outside the reference book.
  - Allow external experience only with attribution, usage/license notes,
    applicability limits, and explicit local-validation status.
  - Preserve historical ledger and setup-report references to the old directory
    rather than rewriting history.
- Validation:
  - Full workspace script suite passed: 142 tests.
  - Focused knowledge, CLI, planner, and startup tests passed: 54 tests.
  - Knowledge registry passed with 20 topics and 66 existing entries.
  - New and legacy knowledge-layer CLI filters both resolve Skill Engineering
    content through the canonical Workspace Engineering layer.
  - The dedicated task route passed at approximately 5,700 initial tokens.
  - Manifest validation passed with 0 errors and 0 warnings.
  - Protocol validation passed with 0 errors; only the established lightweight
    schema-depth warning remains after refresh.
  - Claude boundary hygiene passed with `WORKSPACE_ENGINEERING/` registered.
  - Change-surface planning accepted the knowledge base as the owning
    documentation layer.
  - Git whitespace validation passed.
- Next:
  - Exercise the provenance process on the first real external reference before
    expanding publication tooling.

### TASK-20260620-004 - Add Agent Registration Contract

- Date: 2026-06-20
- Status: completed
- Task type: agent_governance_update, developer_interface_tooling
- Branch: codex/agent-registration-contract
- Commit: f5531ab (core registration contract); documentation/report commit follows
- Read:
  - current Agent governance policy, CLI, tests, task routing, and platform Manifest
  - bounded Cursor and Reasonix evidence in `mcp/README.md`
- Modified:
  - centralized Agent registry, schema, and example contract
  - lifecycle-aware validation and Consumer fallback
  - `workspace agent list/show/validate/doctor`
  - bounded testing-record surface and governance documentation
- Decision:
  - Keep roles, capabilities, surfaces, and leases in the policy; keep concrete
    identity, status, scope, platform references, and lifecycle in the registry.
  - Preserve effective permissions for Codex, Claude Code, OpenCode, and Hermes.
  - Classify Cursor as a proposed Agent host and Reasonix as a proposed tool
    client, with Consumer-only effective access.
  - Do not automate activation, projection changes, leases, worktrees, Session
    cleanup, or external program configuration.
- Validation:
  - Full script test suite passed: 140 tests.
  - Focused Agent governance and workspace CLI suite passed: 44 tests.
  - Task resolution and knowledge registry validation passed.
  - Manifest validation passed with 0 errors and 0 warnings.
  - Protocol validation passed with 0 errors; the remaining schema-depth
    warning is the established repository limitation.
  - Codex, Claude Code, OpenCode, and Hermes doctor checks passed.
  - Cursor and Reasonix returned only expected proposed/Consumer and
    unconfirmed-boundary warnings.
  - Hermes retained diagnosis-record access and remained denied on structural
    Manifest writes.
  - Git whitespace validation passed.
- Next:
  - Run one real bounded candidate experiment before promoting Cursor or
    Reasonix beyond proposed.

### TASK-20260620-003 - Establish external delivery output boundary

- Date: 2026-06-20
- Status: completed
- Task type: shared_policy_update, source_of_truth_dedup, startup_context_optimization
- Branch: main
- Commit: pending
- Read:
  - workspace path, source, staging, reporting, and agent-governance rules
  - manifest absolute-path validation behavior
- Modified:
  - manifest-declared workspace output root
  - external delivery classification and directory layout policy
  - compact always-on routing rule and manifest validation
  - protocol index, workspace/path policy, and current status
- Decision:
  - Separate repository-native artifacts, transient staging files, and final
    external deliverables by purpose.
  - Route new external deliverables by category, month, and task under the
    manifest-declared output root.
  - Preserve existing files under the broader output directory until a
    separately reviewed migration.
- Validation:
  - Manifest validation passed with 0 errors and 0 warnings.
  - Protocol validation passed with 0 errors; only lightweight-schema and
    prior-report freshness warnings were reported.
  - Startup-context regression suite passed: 6 tests.
  - Shared-policy task resolution remained within its required token budget.
  - Git whitespace validation passed.
  - Workspace snapshots regenerated; commit-based freshness remains expectedly
    stale until these source and report changes are committed together.
- Next:
  - Observe real deliverables before adding automation or a dedicated output
    CLI command.

### TASK-20260620-002 - Add agent governance request and lease flow

- Date: 2026-06-20
- Status: completed
- Task type: agent_governance_update, shared_policy_update, developer_interface_tooling
- Branch: main
- Commit: pending
- Read:
  - workspace authority, execution-mode, discovery, failure, and reporting policies
  - current task routing, CLI delegation, platform exposure, and report layouts
- Modified:
  - machine-readable agent role and workspace surface matrix
  - agent governance policy, request inbox, lease schema, and templates
  - `workspace agent` status, check, request, and lease validation commands
  - task and knowledge routing, architecture, current status, and usage guidance
- Decision:
  - Keep skill invocation open without treating exposure as governance authority.
  - Keep Codex and Claude Code as default structural maintainers.
  - Let Hermes and OpenCode write only bounded diagnosis, handoff, and agent
    report scopes by default.
  - Let unregistered agents submit change requests but not modify structure.
  - Require an isolated worktree for any temporary `structural_write` lease.
- Validation:
  - Agent-governance and workspace-CLI focused tests passed: 31 tests.
  - Task resolution and knowledge-registry validation passed.
  - Manifest validation passed with 0 errors and 0 warnings.
  - Protocol validation passed with 0 errors and 2 existing/report-freshness
    warnings.
  - Hermes structural-write denial and bounded runtime-record allowance both
    behaved as designed.
  - Lease schema validation passed; the checked example is intentionally not
    an active authorization.
  - Workspace report refresh remains blocked by the inaccessible transient
    directory `tmpbu24t28b/`; the managed sandbox refused both inspection and
    exact-path deletion.
- Next:
  - Remove `tmpbu24t28b/` from an authorized local shell, then run
    `python scripts/workspace_cli.py reports refresh workspace`.
  - Keep lease issuance, worktree creation, merge, and lease cleanup manual
    until the initial policy has been exercised on real agent requests.

### TASK-20260620-001 - Release workspace v1.3.0

- Date: 2026-06-20
- Status: release_ready
- Task type: governance_summary_tooling, report_regeneration
- Branch: main
- Commit: pending
- Read:
  - workspace manifest, current status, todo, and recent task ledger
  - Git history and tags since `v1.2.0`
  - existing GitHub releases and workspace versioning policy
- Modified:
  - workspace version and current skill inventory
  - release continuity record and deferred changelog decision
  - current manifest, protocol, setup, and health report snapshots
- Decision:
  - Release `v1.3.0` because the workspace gained a complete standalone
    disk-scan governance skill and materially expanded platform exposure.
  - Keep detailed version notes in the GitHub Release instead of adding a
    repository changelog without an established maintenance convention.
- Validation:
  - Manifest validation completed with 0 errors and 0 warnings.
  - Protocol validation completed with 0 errors and 1 known lightweight-schema
    warning.
  - Workspace script tests passed (116), disk-scan-reporter tests passed (35),
    and character-generator tests passed (10).
  - All 15 manifest projections passed link validation.
  - `git diff --check` passed.
- Next:
  - Commit release metadata, confirm post-commit health and report freshness,
    tag `v1.3.0`, push, and publish the GitHub Release.

### TASK-20260619-003 - Align character-system platform exposure

- Date: 2026-06-19
- Status: done
- Task type: skill_architecture_update, platform_exposure
- Branch: main
- Commit: 92e60bc (merge)
- Read:
  - manifest platform roots, skill contracts, and projection inventory
  - four character-system skill entrypoints and workspace exposure policies
  - Claude Code project-skill discovery documentation
- Modified:
  - character-system exposure contracts and projection declarations
  - Claude Code project skill junctions and architecture inventory
  - Codex `style-doctor` and Hermes `style-doctor`/`zyc` projections
  - current workspace status
- Decision:
  - Expose `character-generator` and `character-maintainer` to Codex and Claude
    Code.
  - Expose `style-doctor` and `zyc` to every skill-loading platform currently
    registered by this workspace: Codex, Claude Code, OpenCode, and Hermes.
  - Preserve one manifest-declared source per skill; use junction projections
    instead of source copies.
- Validation:
  - All four character-system skill source contracts pass lifecycle validation.
  - All 15 manifest projections resolve to their declared source directories.
  - Manifest validation reports 0 errors and 0 missing projection warnings.
  - Workspace script tests passed (116), disk-scan-reporter tests passed (35),
    and character-generator tests passed (10).
- Next:
  - Refresh current reports, push `main`, and retire the merged feature branch.

### TASK-20260619-002 - Add disk scan safety and coverage audits

- Date: 2026-06-19
- Status: done
- Task type: skill_architecture_update
- Branch: current worktree
- Commit: pending
- Read:
  - existing disk scanner implementation, tests, manifest contract, and workspace policy
  - Apache-2.0 `bootandy/dust` and MIT `pkolaczk/fclones` reference repositories
- Modified:
  - V1.5 static audit guard, audit policy, allowed-write-root enforcement, and shallow snapshots
  - per-root coverage states plus file-count and elapsed-time budgets
  - report safety and coverage sections, schema reference, tests, and documentation
  - manifest required-file contract and validation snapshot
  - isolated full reference clones under `${WORKSPACE_ROOT}\knowledge\disk_scanner`
- Decision:
  - Keep all scan behavior read-only and fail closed when the production static audit fails.
  - Permit runtime artifacts only under `reports/`, `state/`, or `logs/`, with
    lexical and resolved-path containment checks.
  - Treat coverage relative to configured roots and budgets rather than an
    entire drive; permission-limited and budget-limited results remain explicit.
  - Use shallow snapshots only as anomaly evidence, never as proof that no file
    content changed.
  - Preserve external repositories as isolated references; do not import or
    copy their implementation into the skill.
- Validation:
  - 28 unit tests and Python compilation passed.
  - Static safety audit passed across both production scripts with no findings.
  - Skill Creator and workspace lifecycle validation passed.
  - Default live scan exited 0 with `cleanup_performed=false`, 0 unexpected
    errors, 0 snapshot warnings, and explicit permission-limited coverage for Temp.
  - Manifest validation completed with 0 errors and 0 warnings.
  - All eight manifest projections pass link validation.
- Next:
  - Add exact-path-first ignore rules before any adaptive planning.
  - Keep adaptive scheduling and automation disabled until coverage history is
    available and separately reviewed.

### TASK-20260619-001 - Add and harden read-only disk scan reporter skill

- Date: 2026-06-19
- Status: done
- Task type: skill_architecture_update, platform_exposure
- Branch: current worktree
- Commit: 2c6e83e (initial implementation); 4eabe08 (follow-up hardening);
  ebb762c (V1.5); V1.5.1 pending
- Read:
  - skill-creator contract and UI metadata schema
  - workspace manifest, architecture, path and workspace policies
  - lifecycle tooling, validator, recent task decisions, and comparable standalone skill
- Modified:
  - standalone `skills/disk-scan-reporter` source, configuration, scanner, tests, and documentation
  - manifest role, authority, execution-mode, required-file, and Codex exposure contracts
  - Codex junction projection and architecture inventory
  - follow-up hardening for CLI failure status, lexical link checks, bounded
    diagnostics, accurate large-file ranking, and relative-path reports
  - V1.5.1 categorized scan errors, logical and allocated size accounting,
    hardlink de-duplication, versioned JSON schema, deterministic config
    fingerprint, reader validation, and roundtrip tests
- Decision:
  - Keep the skill standalone because it shares workspace infrastructure but
    has no character-system business dependency.
  - Grant only `environment_audit` authority; permit `record_write` solely for
    generated reports while defaulting to `text_only`.
  - Scan configured paths through metadata only, cap detailed candidates, do
    not follow links by default, and never include a cleanup executor.
  - Default to Downloads and local Temp rather than broad AI-data and workspace
    roots; require explicit configuration for additional roots.
  - Default reports to numbered scan-root labels to reduce disclosure of local
    usernames and directory layouts while retaining absolute paths as opt-in.
- Validation:
  - Skill Creator and workspace lifecycle validation passed.
  - Six temporary-directory unit tests passed.
  - Default configured scan completed with `cleanup_performed=false`; access
    failures and skipped paths were recorded without elevation.
  - Manifest validation completed with 0 errors and 0 warnings.
  - All eight manifest projections pass link validation.
  - Follow-up suite expanded from 6 to 16 tests, including Windows junction,
    invalid-config exit status, unexpected scan failure, depth and record
    limits, Markdown rendering, and report-path privacy coverage.
  - Default live scan completed with exit 0, `cleanup_performed=false`,
    relative path reporting, 0 unexpected errors, and no UserProfile or
    LocalAppData root disclosure in the JSON report.
  - V1.5.1 expanded the suite to 35 passing tests, including Windows junction,
    error category, allocated size, hardlink, config fingerprint, JSON
    roundtrip, and unknown-schema coverage.
  - Python compilation, static safety audit, Skill Creator validation,
    workspace lifecycle validation, manifest validation, and all eight
    projection checks passed.
  - V1.5.1 default live scan exited 0 with `cleanup_performed=false`, relative
    paths, 0 unexpected errors, and explicit partial allocated-size evidence
    when eight files did not expose allocation metadata.
- Next:
  - Keep periodic automation out of this task. If requested later, add it only
    as a separate read-only task that invokes the existing command and
    distributes a privacy-reviewed summary without cleanup actions.

### TASK-20260618-003 - Add opt-in Claude model routing policy

- Date: 2026-06-18
- Status: done
- Task type: task_registry_update, shared_policy_update
- Branch: codex/windows-ai-storage-governor
- Commit: pending
- Read:
  - workspace architecture, shared policy and path boundaries, protocol index
  - Claude project boundary and official CLAUDE.md import behavior
  - current task routing and recent maintenance decisions
- Modified:
  - reusable Claude model-routing policy, integration example, and rationale
  - optional shared-policy discovery index
  - dedicated shared-policy maintenance task route
- Decision:
  - Keep model routing as an opt-in Policy rather than a Skill or always-loaded
    global rule.
  - Use `deepseek-v4-flash` by default and recommend `deepseek-v4-pro` for
    complex or high-risk work.
  - Require explicit confirmation before high-risk modification; do not
    implement automatic model switching or change provider configuration.
- Validation:
  - Shared policy task resolution passed at 4,479 initial tokens.
  - Resolver and startup-context tests passed (31).
  - Protocol validation completed with 0 errors and the two existing
    lightweight-schema and pre-run freshness warnings.
  - Task registry smoke resolutions and `git diff --check` passed.
  - Disposable Claude Code project tests routed README optimization and
    bounded read-only repository analysis to Flash, and routed a three-file
    training-flow change and Git rebase conflict resolution to Pro.
  - External imports required the Policy directory to be granted through
    `--add-dir`; the integration example and README now document that
    prerequisite.
- Next:
  - Adopt the policy project by project through explicit CLAUDE.md imports.
  - Add complexity-analysis tooling only as a separate evidence-producing
    layer that remains subordinate to the Policy.

### TASK-20260618-002 - Forward-audit Gemini npm and Playwright storage

- Date: 2026-06-18
- Status: done
- Task type: skill_architecture_update
- Branch: codex/windows-ai-storage-governor
- Commit: pending
- Read:
  - Windows AI storage governor workflow, classification, adapter, and report contracts
  - live command locations and bounded Gemini, npm, and Playwright storage metadata
  - current Gemini CLI, npm, and Playwright primary documentation
- Modified:
  - tool-aware audit classification and command observations
  - Gemini, npm, and Playwright adapter guidance and report schema
  - safe fixture cases for npm global data and Playwright registration metadata
- Decision:
  - Preserve the existing Gemini user-home junction to the data drive.
  - Classify npm cache, prefix, and global package root as separate cache and
    runtime/install surfaces; do not mistake global `node_modules` for project source.
  - Treat the small `%LOCALAPPDATA%\ms-playwright\b\browser@*` directory as
    live registration metadata when that bounded shape is observed.
  - Preserve all currently observed paths; no migration or cleanup action is justified.
- Validation:
  - Live audit reported 8 findings: 7 preserve, 1 report-only, 0 migration
    candidates, and 0 blocked findings.
  - Gemini, Codex, and Claude user-profile entries are stable links to data-drive targets.
  - npm cache and global install data resolve to the data drive.
  - `PLAYWRIGHT_BROWSERS_PATH` resolves to the data drive; the standalone
    `playwright` command is absent, so browser launch verification remains optional.
- Next:
  - Add a guarded apply executor only after a real approved migration plan
    demonstrates the need.

### TASK-20260618-001 - Add Windows AI storage governance skill

- Date: 2026-06-18
- Status: done
- Task type: skill_architecture_update, platform_exposure
- Branch: codex/windows-ai-storage-governor
- Commit: pending
- Read:
  - skill-creator instructions and UI metadata contract
  - workspace manifest, architecture, path policy, workspace policy, and recent ledger
  - skill architecture patterns, anti-patterns, lifecycle tooling, and Claude Code skill documentation
- Modified:
  - standalone `skills/windows-ai-storage-governor` source, references, scripts, fixture, and Codex metadata
  - manifest role, authority, execution-mode, and Codex/Claude exposure contracts
  - manifest and lifecycle validation for governance and environment-write semantics
  - workspace architecture, current status, policy, and projection ignore boundary
- Decision:
  - Keep one source skill with Codex and Claude Code junction projections.
  - Default to audit and plan; require exact approval for apply and separate
    confirmation for cleanup.
  - Add narrow `governance`, `environment_audit`,
    `environment_migration_apply`, and `environment_write` contracts instead
    of mislabeling external storage governance as source maintenance.
  - Ship no automatic destructive cleanup executor in the MVP.
- Validation:
  - Skill Creator validation and workspace skill lifecycle validation passed.
  - PowerShell parsing and safe staging fixture audit/plan/verify runs passed.
  - Manifest validation completed with 0 errors and 0 warnings.
  - All seven manifest projections pass link validation.
  - Codex and Claude Code registries resolve the new skill to the same source.
- Next:
  - Forward-test real audit and migration-plan prompts before adding a guarded
    apply executor or more tool-specific adapters.

### TASK-20260616-001 - Make Claude boundary failures actionable

- Date: 2026-06-16
- Status: done
- Task type: claude_project_boundary
- Branch: main
- Commit: commit containing this entry
- Read:
  - workspace and CNN Claude instructions, settings, hooks, and launchers
  - current project registry and both Git roots
  - reported Markdown failure and native-tool denial sequence
- Modified:
  - workspace Claude boundary hook and regression tests
  - Claude startup, project-switching, and failure guidance
  - current project memory
- Decision:
  - Keep repository isolation: a workspace session must not silently become a
    CNN session.
  - Support direct `claude` startup from any target Git root; named launchers
    remain optional conveniences.
  - Treat blocked native editing as a project-root mismatch that requires a new
    session, not as permission to rewrite files through PowerShell.
- Validation:
  - Native workspace edits pass the workspace boundary hook.
  - Native CNN edits pass the CNN repository's own boundary hook.
  - Native external edits from a workspace session are denied with restart
    guidance.
  - PowerShell-wrapped `Set-Content` writes to CNN are denied by the workspace
    hook instead of bypassing native editor restrictions.
  - Both registered launchers report Claude Code 2.1.177 from the correct Git
    roots.
  - Workspace script tests passed (115); full workspace health passed.
  - Task resolution and `git diff --check` passed.
- Next:
  - Start Claude directly from the target Git root or use a registered launcher;
    do not switch repositories inside an active session.

### TASK-20260615-003 - Reconcile active project memory

- Date: 2026-06-15
- Status: done
- Task type: task_registry_update, project_memory_maintenance
- Branch: main
- Commit: commit containing this entry
- Read:
  - current status, todo, recent ledger entries, and session handoff
  - task resolver authority, context budgets, and current Git history
- Modified:
  - dedicated project-memory maintenance task route
  - todo classification and context-efficiency evidence
  - recent ledger commit and next-action metadata
- Decision:
  - Keep always-on rules out of Todo and route them through existing startup,
    context-budget, and shared-policy entry points.
  - Record context measurements only when they reveal a meaningful outlier or
    missing route.
  - Do not fabricate runtime-loop cases or package boundaries before a real
    event or unrelated skill requires them.
- Validation:
  - The new project-memory route resolves at 2,914 exact `o200k_base` tokens.
  - Resolver and startup-context tests passed (31).
  - Full workspace script test discovery passed (112).
  - Workspace summary reports 23 task routes and clean recent governance
    metadata for the five newest entries.
  - Full workspace health with tests passed; reports and projections remain
    fresh and valid.
  - `git diff --check` passed.
- Next:
  - Use the new route for future status, todo, and handoff reconciliation.

### TASK-20260615-002 - Expand the role-oriented work index

- Date: 2026-06-15
- Status: done
- Task type: knowledge_interface_tooling, prompt_usage_update
- Branch: main
- Commit: add5a10
- Read:
  - knowledge registry and knowledge finder tests
  - role-oriented usage references and user entry points
  - task validation and recent maintenance ledger
- Modified:
  - bounded knowledge routes for runtime use, engineering operations, workflows,
    and platform loading
  - knowledge route tests and future validation commands
  - the usage reference index and top-level usage navigation
- Decision:
  - Keep `workspace_manifest.yaml` authoritative for current source and exposure
    facts while indexing the smallest useful role-oriented guidance files.
  - Separate platform loading guidance from platform exposure policy so a
    platform name does not imply skill ownership.
  - Add a local `REFERENCE/README.md` instead of requiring users or agents to
    infer the meaning of the four reference subdirectories.
- Validation:
  - Knowledge registry validation passed with 18 topics and 57 existing entries.
  - Runtime usage, character generation, platform loading, and workflow queries
    resolve to their intended role-oriented guidance.
  - Knowledge and workspace CLI tests passed (33).
  - All five manifest projections pass link validation.
  - Full workspace health with tests passed; all report groups remain fresh.
  - All task prompt ids still resolve and `git diff --check` passed.
- Next:
  - Observe these routes during normal maintenance and add aliases only from
    demonstrated lookup misses.

### TASK-20260615-001 - Remove platform ownership residue

- Date: 2026-06-15
- Status: done
- Task type: source_of_truth_dedup, cleanup_migration
- Branch: main
- Commit: 5051629
- Read:
  - active non-report Codex/OpenCode references
  - current platform debug paths and MCP client registrations
  - merged local and remote branch ancestry
  - role-oriented usage and character-system architecture
- Modified:
  - role-oriented usage references and general maintenance wording
  - OpenCode MCP and quick-start path facts
  - task validation command and knowledge/prompt labels
  - current release handoff state
- Decision:
  - Keep platform names only where they identify a real loading surface,
    projection, client command, session store, or platform-specific guide.
  - Replace platform-as-owner wording with runtime, engineering, maintainer, or
    compatible-agent terminology.
  - Organize skill references by runtime and engineering role; keep platform
    safety notes under a dedicated `REFERENCE/platforms/` layer.
  - Delete merged local work branches after this commit; delete the merged
    remote legacy branch only with an explicit push operation.
- Validation:
  - Workspace script tests passed (108); character-generator tests passed (10).
  - All four registered skills pass lifecycle validation.
  - Manifest validation completed with 0 errors and 0 warnings.
  - Protocol validation completed with 0 errors; only the known lightweight
    schema warning remains after report refresh.
  - All five manifest projections pass link validation.
  - `opencode debug skill` still discovers `style-doctor` and `zyc`.
  - Old platform-owned reference paths, retired CLI placeholders, and selected
    platform-as-maintainer phrases have no active non-report matches.
- Next:
  - No remaining local or remote work branches require cleanup.

### TASK-20260614-004 - Migrate character skills into a domain package

- Date: 2026-06-14
- Status: done
- Task type: skill_architecture_update, platform_exposure, source_of_truth_dedup
- Branch: main
- Commit: d88e18c
- Release: v1.2.0
- Read:
  - workspace manifest, architecture, package guidance, and protocol policies
  - four core skill entrypoints and source layouts
  - manifest, protocol, report, projection, and change-planning scripts
  - current Codex/OpenCode junction targets and OpenCode discovery output
- Modified:
  - character-system runtime, engineering, shared, and report directory layout
  - manifest package registry, skill source paths, protocol dependencies, and projection targets
  - package-aware validators, reports, CI, task routing, knowledge routing, and Claude boundary policy
  - prompt template paths and active workspace documentation
  - five platform junctions declared by the manifest
  - session continuity policy, migration registry, read-only audit command, and external Claude/OpenCode backups
- Decision:
  - Organize source by domain and lifecycle role rather than by Codex/OpenCode.
  - Keep user-facing character skills under package `runtime/` and generation, diagnosis, and maintenance tools under `engineering/`.
  - Keep workspace governance in root `shared/` and character-only protocols in package-local `shared/`.
  - Reserve root `skills/` for unrelated standalone skills.
  - Preserve legacy manifest exposure aliases until consumers fully migrate to `exposures[]`.
  - Keep historical session directory fields unchanged; protect recovery with
    tool-native exports, consistent external snapshots, and explicit path mappings.
- Validation:
  - Manifest validation completed with 0 structural errors before junction refresh.
  - Character-system protocol validation completed with 0 errors.
  - Workspace script tests passed (108); character-generator tests passed (10).
  - All five manifest projections were rebuilt and pass link validation.
  - OpenCode `debug skill` discovers `style-doctor` and `zyc` through the new package paths.
  - Local ignored writerA output moved with the generator and retains 29 files totaling 33,112 bytes.
  - Claude workspace transcripts were backed up as 5 JSONL files with SHA-256
    metadata; no skill-subdirectory Claude project bucket was found.
  - Seven OpenCode sessions tied to the old ZYC test path were exported, and a
    consistent SQLite backup was created before further migration work.
  - All four registered skills pass lifecycle validation; all five projections
    pass link validation.
  - Session continuity audit passes with 5/5 Claude transcripts and 7/7
    OpenCode sessions plus exports available.
- Next:
  - Observe the released package layout before considering another migration.

### TASK-20260614-003 - Add skill lifecycle CLI

- Date: 2026-06-14
- Status: done
- Task type: skill_lifecycle_tooling, developer_interface_tooling
- Branch: main
- Commit: 059e4e2
- Read:
  - workspace manifest skill and projection contracts
  - unified workspace CLI and delegation tests
  - existing projection setup behavior and workspace CLI quick start
- Modified:
  - manifest-aware skill lifecycle implementation and focused tests
  - unified `workspace skill` command delegation
  - task routing and beginner-facing CLI documentation
- Decision:
  - Keep `skill init` source-only; manifest registration remains an explicit reviewed step.
  - Let `skill expose` preview by default and require `--apply` for platform writes.
  - Ship the lifecycle CLI with the character-package migration because its
    manifest-aware paths and package layout are validated together.
  - Preserve real directories, incorrect links, and broken junctions instead of replacing them automatically.
  - Support validation by either registered skill id or registered source path.
- Validation:
  - Focused lifecycle and CLI delegation tests passed (29).
  - Full workspace script test discovery passed (105).
  - Python compile checks and command help smoke tests passed.
  - Registered skills validate by both id and manifest source path.
  - Skill list and expose preview preserve five migration-stale platform junctions as `BLOCKED_EXISTING_ITEM`.
  - No `skill expose --apply` command was run and no platform directory was modified.
  - `skill_lifecycle_tooling` resolves with a measured 8054-token initial context under its 9000-token warning budget.
  - `git diff --check` passed.
- Next:
  - Use the lifecycle CLI on the next unrelated skill before extending it.

### TASK-20260614-002 - Correct governance metadata and knowledge routing

- Date: 2026-06-14
- Status: done
- Task type: governance_summary_tooling, knowledge_interface_tooling, source_of_truth_dedup
- Branch: main
- Commit: 537a041
- Read:
  - governance summary and knowledge interface task resolutions
  - current Git tags, manifest version, recent ledger entries, and historical PROJECT_CONTEXT setup report
  - Claude Code workspace boundary and project-switching guidance
- Modified:
  - workspace summary tag selection and focused tests
  - bounded knowledge aliases and project-boundary topic
  - historical setup report status banner
  - completed-task commit references
- Decision:
  - Anchor workspace version reporting to the manifest-declared `v<workspace_version>` tag.
  - Do not let a nearer component release tag redefine workspace version state.
  - Preserve the original PROJECT_CONTEXT setup report as visibly superseded historical evidence.
  - Route common Chinese boundary and runtime-drift queries without broad workspace scanning.
- Validation:
  - Governance summary and knowledge interface task resolution passed within context budgets.
  - Workspace summary tests and CLI delegation tests passed (20).
  - Knowledge finder and CLI delegation tests passed (24).
  - Full workspace script test discovery passed (91).
  - Knowledge registry validation passed with 13 topics and 33 existing entries.
  - `项目边界`, `Claude 串仓`, and `运行时漂移` each resolve to the intended bounded topic.
  - Workspace summary reports manifest version and workspace tag as `1.1.0` / `v1.1.0`.
  - `workspace health --with-tests` returned `PASS`.
  - `git diff --check` passed.
- Next:
  - No follow-up required unless workspace version reporting regresses.

### TASK-20260614-001 - Complete PROJECT_CONTEXT disassembly migration

- Date: 2026-06-14
- Status: done
- Task type: task_registry_update, source_of_truth_dedup, report_regeneration
- Branch: 0613_claude
- Commit: d568fe2
- Read:
  - PROJECT_CONTEXT task, knowledge, status, todo, and recent ledger context
  - root architecture and workspace manifest
  - workspace path and reporting policies
  - SKILL_ENGINEERING workspace, portability, and governance patterns
- Modified:
  - active task and knowledge registry references
  - completed PROJECT_CONTEXT todo entries
  - machine-local path examples in reusable SKILL_ENGINEERING guidance
  - workspace and Claude Code quick-start path examples
  - current manifest, protocol, setup, and health report snapshots
- Decision:
  - Route workspace purpose and architecture through root `ARCHITECTURE.md`.
  - Preserve deleted PROJECT_CONTEXT paths only in historical ledger and snapshot evidence.
  - Keep concrete machine-local deployment paths centralized in `workspace_manifest.yaml`.
  - Regenerate current reports from source instead of manually editing generated conclusions.
- Validation:
  - Task resolution completed without missing required resources.
  - Knowledge registry validation passed with 12 topics and 30 existing entries.
  - Manifest validation completed with 0 errors and 0 warnings.
  - Protocol validation completed with 0 errors and 1 expected lightweight-schema warning.
  - Workspace reports were regenerated; required missing and projection drift counts are 0.
  - Script tests passed (87); character-generator tests passed (10).
  - Python compile checks and all five projection link checks passed.
  - Reusable SKILL_ENGINEERING and quick-start docs contain no machine-local absolute paths.
  - `git diff --check` passed.
- Next:
  - Confirm report freshness after commit, then merge into `main`.

### TASK-20260613-004 - Separate CNN and workspace Claude project roots

- Date: 2026-06-13
- Status: done
- Task type: claude_project_boundary
- Branch: codex/claude-project-boundaries
- Commit: 2a37043
- Read:
  - workspace Git history and Claude session cwd evidence
  - the standalone CNN repository README and Git state
  - Claude Code project instruction, rules, settings, and hook conventions
- Modified:
  - workspace Claude boundary files, health checks, context, and usage guide
  - standalone CNN `claude/` implementation and project boundary files
  - machine-local Claude project alias registry and launchers
- Decision:
  - Treat Claude Code startup cwd as the project selector; do not use the workspace manifest as an external-project registry.
  - Keep the skill workspace and CNN project as separate Git roots.
  - Block unregistered workspace top-level projects and cross-repository writes through tracked hooks.
  - Preserve the six-stage CNN development history by replaying it in the real CNN repository.
- Validation:
  - The six CNN development commits were replayed into the standalone CNN repository.
  - CNN Python files passed `compileall`; model and Claude settings JSON files parsed successfully.
  - The CNN boundary hook allowed in-repository writes and blocked writes to the workspace.
  - Full CNN pytest collection is currently blocked by a fatal NumPy/Torch BLAS initialization failure in the active Anaconda environment.
  - Workspace boundary hooks allow registered-layer writes and block both root `claude/` creation and cross-repository writes.
  - All seven focused health tests passed.
  - `workspace health --with-tests` returned `PASS`.
  - Both `claude-workspace --version` and `claude-cnn --version` resolved the intended Git roots.
  - `git diff --check` passed.
- Next:
  - Merge the clean workspace governance branch after review.
  - Repair the CNN Python runtime before treating the prototype tests as fully validated.

### TASK-20260613-003 - Govern agent and test runtime metadata

- Date: 2026-06-13
- Status: done
- Task type: startup_context_optimization
- Branch: codex/claude-project-boundaries
- Commit: c4b6534
- Read:
  - root and nested agent instruction entry points
  - Claude Code project-local settings
  - pytest cache behavior and current CI configuration
- Modified:
  - .gitignore
  - pytest.ini
  - codex/character-generator/CLAUDE.md
  - scripts/workspace_health.py
  - scripts/tests/test_workspace_health.py
  - PROJECT_CONTEXT/task_ledger.md
  - local ignored `.claude/settings.local.json` and `.pytest_cache/`
- Decision:
  - Add a Claude bridge only where an independent nested `AGENTS.md` exists.
  - Keep shared Claude instructions trackable while ignoring project-local Claude state.
  - Disable pytest cache generation and detect common root Python tool caches during health checks.
  - Remove the broad local `git checkout` permission instead of preserving it.
- Validation:
  - All 95 pytest tests passed with the cache provider disabled.
  - Running pytest did not recreate `.pytest_cache`.
  - Six focused workspace health tests passed.
  - `workspace health --with-tests` returned `PASS`, including the new hygiene check.
  - Git ignore rules matched Claude local state and Python tool cache paths.
  - `git diff --check` passed.
- Next:
  - Let tool-local metadata reappear only when explicitly needed and keep it ignored.
  - Use `workspace health` to catch root runtime cache regressions.

### TASK-20260613-002 - Add Claude Code handoff compatibility

- Date: 2026-06-13
- Status: done
- Task type: startup_context_optimization
- Branch: codex/claude-project-boundaries
- Commit: a467811
- Read:
  - Claude Code project-instruction and settings conventions
  - current Git branch, merge base, and remote tracking state
  - current status, todo, and session handoff memory
- Modified:
  - CLAUDE.md
  - PROJECT_CONTEXT/current_status.md
  - PROJECT_CONTEXT/todo.md
  - PROJECT_CONTEXT/session_handoff.md
  - PROJECT_CONTEXT/task_ledger.md
- Decision:
  - Import `AGENTS.md` from Claude's native project instruction entry point instead of copying policy.
  - Keep Claude auto memory local and keep durable handoff facts in tracked workspace sources.
  - Require branch and merge-base checks before one agent continues another agent's work.
  - Do not treat an agent-named workspace folder as external-project registration.
- Validation:
  - Root `CLAUDE.md` imports `AGENTS.md` without duplicating its policy.
  - The active feature branch has current `main` as an ancestor.
  - `workspace health --with-tests` returned `PASS`.
  - All changed Markdown files decoded as UTF-8 with no replacement characters.
  - `git diff --check` passed.
- Next:
  - Use the remote-tracked feature branch when another machine or agent needs to continue it.
  - Observe real Codex-to-Claude and Claude-to-Codex handoffs before adding hooks.

### TASK-20260613-001 - Add live governance summary

- Date: 2026-06-13
- Status: done
- Task type: governance_summary_tooling
- Branch: codex/governance-summary-p2-5
- Commit: f30ca0b
- Read:
  - workspace manifest identity and inventory
  - current Git branch, tag, commit, and working-tree state
  - bounded recent task ledger entries
  - workspace CLI parser command surface
- Modified:
  - README.md
  - PROJECT_CONTEXT/task_registry.yaml
  - PROJECT_CONTEXT/task_ledger.md
  - USAGE_GUIDES/QUICK_START/workspace_cli.md
  - scripts/workspace_summary.py
  - scripts/tests/test_workspace_summary.py
  - scripts/workspace_cli.py
  - scripts/tests/test_workspace_cli.py
- Decision:
  - Derive live facts from manifest, Git, registries, and the bounded ledger instead of creating another changelog or report.
  - Derive the command inventory from the CLI parser so documentation cannot become its source of truth.
  - Keep text and JSON output read-only and uncached.
- Validation:
  - The dedicated task route resolved with `PASS` at 5,105 initial tokens using exact `o200k_base` counting.
  - Moving the ledger and knowledge registry to optional context reduced the first route result from 14,967 tokens and `WARN`.
  - All 84 script tests passed.
  - `workspace health --with-tests` returned `PASS`.
  - Text output and PowerShell JSON parsing both succeeded.
  - The updated Chinese guide remained valid UTF-8 with no replacement characters.
  - `git diff --check` passed.
- Next:
  - Use the summary during ordinary maintenance before adding more governance commands.
  - Treat the current single-agent developer CLI roadmap as complete and enter an observation period.

### TASK-20260612-010 - Add managed workspace launcher

- Date: 2026-06-12
- Status: done
- Task type: workspace_launcher_tooling
- Branch: codex/workspace-launcher-p2-4
- Commit: 501c8bb
- Read:
  - current user PATH and PowerShell command resolution
  - existing workspace CLI guide and command surface
- Modified:
  - README.md
  - PROJECT_CONTEXT/task_ledger.md
  - PROJECT_CONTEXT/task_registry.yaml
  - USAGE_GUIDES/QUICK_START/workspace_cli.md
  - scripts/workspace_launcher.py
  - scripts/tests/test_workspace_launcher.py
  - scripts/workspace_cli.py
  - scripts/tests/test_workspace_cli.py
  - scripts/workspace_health.py
  - managed user-local `workspace.cmd` after validation
- Decision:
  - Install into the existing user-local bin instead of editing PowerShell profiles or system PATH.
  - Mark launcher ownership and block overwrite or removal of unmanaged commands.
  - Keep install, status, uninstall, and dry-run available through the CLI.
- Validation:
  - The dedicated task route resolved with `PASS` at 2,738 initial tokens using exact `o200k_base` counting.
  - The default target had no conflicting command and was already on the user PATH.
  - The installed launcher resolved from the user home directory and ran health and Chinese knowledge queries outside the workspace.
  - Managed self-uninstall returned exit code 0, removed the launcher after process exit, and reinstall restored it.
  - Unmanaged launcher tests block replacement and deletion.
  - Exact launcher-path propagation prevents child test processes from mistaking temporary launchers for the active command.
  - All 80 script tests passed and `workspace health --with-tests` returned `PASS`.
  - The updated Chinese guide remained valid UTF-8 with no replacement characters.
  - `git diff --check` passed.
- Next:
  - Use `workspace ...` as the normal developer entry point.
  - Treat governance/version summaries as optional polish after a period of normal use.

### TASK-20260612-009 - Add developer failure diagnostics

- Date: 2026-06-12
- Status: done
- Task type: failure_diagnostics_tooling
- Branch: codex/failure-check-p2-3
- Commit: 55d56ff
- Read:
  - shared/failure_policy.md
  - resolver resource finding and placeholder contracts
- Modified:
  - README.md
  - PROJECT_CONTEXT/task_ledger.md
  - PROJECT_CONTEXT/task_registry.yaml
  - USAGE_GUIDES/QUICK_START/workspace_cli.md
  - scripts/failure_check.py
  - scripts/tests/test_failure_check.py
  - scripts/workspace_cli.py
  - scripts/tests/test_workspace_cli.py
- Decision:
  - Reuse resolver findings instead of creating a second required/optional policy.
  - Present task state as `READY`, `DEGRADED`, or `BLOCKED`.
  - Keep diagnostics read-only and forbid guessed or out-of-workspace replacement paths.
- Validation:
  - The dedicated task route resolved with `PASS` at 3,311 initial tokens using exact `o200k_base` counting.
  - A correctly bound metadata task returned `READY`.
  - The same task without its required binding returned `BLOCKED`, exit code 1, and the exact `--bind` action.
  - Unit coverage verifies optional missing resources become `DEGRADED` and path escapes never trigger broad search.
  - All 73 script tests passed and `health --with-tests` remained `PASS`.
  - The updated Chinese guide remained valid UTF-8 with no replacement characters.
  - `git diff --check` passed.
- Next:
  - Use `failure check` after resolver errors instead of manually guessing missing paths.
  - Consider the direct PowerShell `workspace` launcher as the next separate convenience item.

### TASK-20260612-008 - Add live workspace health command

- Date: 2026-06-12
- Status: done
- Task type: workspace_health_tooling
- Branch: codex/workspace-health-p2-2
- Commit: fa27225
- Read:
  - existing bootstrap, knowledge, report, and link checker output contracts
  - workspace CLI beginner guide
- Modified:
  - README.md
  - PROJECT_CONTEXT/task_ledger.md
  - PROJECT_CONTEXT/task_registry.yaml
  - USAGE_GUIDES/QUICK_START/workspace_cli.md
  - scripts/workspace_health.py
  - scripts/tests/test_workspace_health.py
  - scripts/workspace_cli.py
  - scripts/tests/test_workspace_cli.py
- Decision:
  - Aggregate existing checks instead of copying their validation logic.
  - Keep health read-only and make the full script suite opt-in through `--with-tests`.
  - Do not treat a dirty Git worktree as infrastructure failure.
- Validation:
  - The dedicated task route resolved with `PASS` at 2,757 initial tokens using exact `o200k_base` counting.
  - Default live health passed bootstrap, 12-topic/31-entry knowledge validation, 3 report groups, and all projection links.
  - `health --with-tests` passed and the full suite reached 67 passing script tests.
  - Stale-report and invalid-output regression tests produce `NEEDS_ATTENTION` and `ERROR` instead of false success.
  - The updated Chinese guide remained valid UTF-8 with no replacement characters.
  - `git diff --check` passed.
- Next:
  - Use default `health` for quick checks and `health --with-tests` before larger commits.
  - Implement failure diagnostics only as the next separate CLI item.

### TASK-20260612-007 - Add beginner workspace CLI guide

- Date: 2026-06-12
- Status: done
- Task type: prompt_usage_update
- Branch: codex/workspace-cli-beginner-guide
- Commit: 1b3e183
- Read:
  - USAGE_GUIDES/README.md
  - USAGE_GUIDES/START_HERE.md
  - current workspace CLI help output
- Modified:
  - USAGE_GUIDES/README.md
  - USAGE_GUIDES/START_HERE.md
  - USAGE_GUIDES/QUICK_START/workspace_cli.md
  - PROJECT_CONTEXT/task_ledger.md
- Decision:
  - Explain the CLI as a local maintenance console rather than an autonomous coding agent.
  - Separate read-only commands from commands that refresh generated reports.
  - Document current capabilities separately from future roadmap candidates.
- Validation:
  - All 62 workspace script tests passed before the guide edit.
  - The documented task, knowledge, prompt, report-status, link-validation, and help commands returned successfully.
  - Unicode code-point checks confirmed the guide contains valid Chinese text with no replacement characters.
  - Strict report freshness and all five platform projection checks passed.
  - `git diff --check` passed.
- Next:
  - Let a beginner use the guide during normal maintenance before adding more explanation.
  - Consider a direct `workspace` PowerShell launcher as a separate convenience task.

### TASK-20260612-006 - Refresh merged workspace reports

- Date: 2026-06-12
- Status: done
- Task type: report_regeneration
- Branch: main
- Commit: 44a5393
- Read:
  - workspace_manifest.yaml
  - shared/reporting_policy.md
- Modified:
  - reports/manifest_validation_report.md
  - reports/protocol_validation_report.md
  - reports/workspace_health_report.md
  - reports/workspace_setup_report.md
- Decision:
  - Regenerate stale current-state reports through their existing generators after merging reporting policy changes.
  - Keep report contents as snapshots and retain manifest, shared policy, and current Git state as authority.
- Validation:
  - Manifest validation completed with 0 errors and 0 warnings.
  - Protocol validation completed with 0 errors and 2 informational warnings.
  - Strict report freshness marked all current report groups `FRESH`.
  - All five manifest projections passed link validation.
- Next:
  - Use explicit report refresh after future relevant source or policy changes.

### TASK-20260612-005 - Fix cross-platform path classification

- Date: 2026-06-12
- Status: done
- Task type: change_surface_planning
- Branch: main
- Commit: 6c999b1
- Read:
  - PROJECT_CONTEXT/change_surface_policy.md
  - scripts/plan_change_surface.py
  - scripts/tests/test_plan_change_surface.py
- Modified:
  - scripts/plan_change_surface.py
  - scripts/tests/test_plan_change_surface.py
- Decision:
  - Detect both Windows and POSIX absolute paths independently of the host operating system.
  - Keep absolute and platform-facing paths blocked as source edit targets.
- Validation:
  - The planner test suite passed with 8 tests.
  - All 62 script tests and 9 character-generator tests passed.
  - Windows drive, Windows UNC, and POSIX absolute paths classify as `external_or_projection`.
  - Repository-relative paths retain their existing source-layer classification.
  - Python syntax compilation and `git diff --check` passed.
- Next:
  - Keep cross-platform path tests whenever planner path rules change.

### TASK-20260612-004 - Add bounded knowledge discovery

- Date: 2026-06-12
- Status: done
- Task type: knowledge_interface_tooling
- Branch: codex/knowledge-find-p2-1
- Commit: 1ebede5
- Read:
  - PROJECT_CONTEXT/README.md
  - SKILL_ENGINEERING/README.md
  - current knowledge-layer filenames and existing indexes
- Modified:
  - AGENTS.md
  - README.md
  - PROJECT_CONTEXT/README.md
  - PROJECT_CONTEXT/knowledge_registry.yaml
  - PROJECT_CONTEXT/task_ledger.md
  - PROJECT_CONTEXT/task_registry.yaml
  - scripts/find_knowledge.py
  - scripts/tests/test_find_knowledge.py
  - scripts/workspace_cli.py
  - scripts/tests/test_workspace_cli.py
- Decision:
  - Index knowledge topics without copying source facts into another truth layer.
  - Search only registry metadata and return paths before loading content.
  - Include Chinese aliases for the user's normal maintenance vocabulary.
- Validation:
  - The dedicated task route resolved with `PASS` at 4,903 initial tokens using exact `o200k_base` counting.
  - The registry contains 12 topics and 31 existing entry paths with no warnings.
  - Chinese aliases for skill development, project status, and failure handling resolved to the intended topics.
  - Exact aliases suppress low-score generic matches.
  - All 61 script tests passed.
  - Strict report freshness and all five projection link checks passed.
  - `git diff --check` passed.
- Next:
  - Use `knowledge find` when task resolution does not already identify the needed knowledge layer.
  - Add topics only when a repeated discovery need appears; do not turn the registry into copied documentation.

### TASK-20260612-003 - Add change-surface planning

- Date: 2026-06-12
- Status: done
- Task type: change_surface_planning
- Branch: codex/change-surface-p1-3
- Commit: 5212dca
- Read:
  - PROJECT_CONTEXT/architecture.md
  - existing task write scopes
  - shared/workspace_policy.md
  - shared/workspace_path_policy.md
- Modified:
  - AGENTS.md
  - README.md
  - PROJECT_CONTEXT/README.md
  - PROJECT_CONTEXT/change_surface_policy.md
  - PROJECT_CONTEXT/task_ledger.md
  - PROJECT_CONTEXT/task_registry.yaml
  - scripts/plan_change_surface.py
  - scripts/tests/test_plan_change_surface.py
  - scripts/workspace_cli.py
  - scripts/tests/test_workspace_cli.py
- Decision:
  - Require an exact task id and explicit intent instead of inferring purpose from filenames.
  - Compare named candidate file sets against resolved write authority and ownership layers.
  - Keep planning read-only and treat recommendations as investigation starting points.
- Validation:
  - The dedicated task route resolved with `PASS` at 7,507 initial tokens using exact `o200k_base` counting.
  - All 52 script tests passed.
  - Automatic planning selected skill source for metadata work and routing registry for task-routing work.
  - Explicit option comparison preferred implementation plus tests over documentation-only changes.
  - Absolute platform paths and report-only substitutes were blocked.
  - Strict report freshness and all five projection link checks passed.
  - `git diff --check` passed.
- Next:
  - Observe planner recommendations during real maintenance before adding more intent types.
  - Keep semantic dependency inspection and validation evidence as the final decision authority.

### TASK-20260612-002 - Add report freshness and explicit refresh interface

- Date: 2026-06-12
- Status: done
- Task type: report_freshness_tooling
- Branch: codex/workspace-cli-p1-1
- Commit: 3e9940a
- Read:
  - shared/reporting_policy.md
  - existing report headers and generators
  - workspace report task and prompt routing
- Modified:
  - README.md
  - PROJECT_CONTEXT/task_ledger.md
  - PROJECT_CONTEXT/task_registry.yaml
  - shared/reporting_policy.md
  - scripts/report_status.py
  - scripts/tests/test_report_status.py
  - scripts/workspace_cli.py
  - scripts/tests/test_workspace_cli.py
- Decision:
  - Keep report status checks read-only.
  - Require an explicit `reports refresh` command before any snapshot is rewritten.
  - Limit the first freshness registry to manifest validation, protocol validation, and current workspace reports.
- Validation:
  - The dedicated task route resolved with `PASS` at 6,252 initial tokens using exact `o200k_base` counting.
  - All 44 script tests passed.
  - Strict report status marked manifest validation, protocol validation, and workspace reports as `FRESH`.
  - Manifest validation completed with 0 errors and 0 warnings.
  - Protocol validation completed with 0 errors and the existing lightweight-schema warning.
  - All five platform projections passed the read-only link check.
  - `git diff --check` passed apart from Git's existing line-ending notices for generated reports.
- Next:
  - Use `reports status --strict` before relying on snapshot conclusions.
  - Continue with change-surface planning only as a separate flow item.

### TASK-20260612-001 - Add unified workspace developer CLI

- Date: 2026-06-12
- Status: done
- Task type: developer_interface_tooling
- Branch: codex/workspace-cli-p1-1
- Commit: 3e9940a
- Read:
  - AGENTS.md
  - PROJECT_CONTEXT/task_registry.yaml
  - PROJECT_CONTEXT/context_budget.md
  - existing resolver, bootstrap, and validation entry points
- Modified:
  - README.md
  - PROJECT_CONTEXT/task_ledger.md
  - PROJECT_CONTEXT/task_registry.yaml
  - scripts/workspace_cli.py
  - scripts/tests/test_workspace_cli.py
- Decision:
  - Add one thin developer entry point that delegates to existing tools.
  - Keep task and prompt resolution logic in `scripts/resolve_task_context.py`.
  - Defer report freshness, knowledge search, and change-surface planning to later flow items.
- Validation:
  - The dedicated task route resolved with `PASS` at 2,435 initial tokens using exact `o200k_base` counting.
  - All 37 script tests passed.
  - Task, prompt, bootstrap, and strict-preflight delegation passed focused tests.
  - All five manifest projections passed the read-only link check.
  - `git diff --check` passed.
- Next:
  - Observe the CLI in normal maintenance work before expanding it.
  - Continue with report freshness only as the next separate flow item.

### TASK-20260611-003 - Restore OpenCode source-linked projections

- Date: 2026-06-11
- Status: done
- Task type: platform_exposure
- Branch: codex/opencode-projection-p0
- Commit: a1db0ba
- Read:
  - workspace_manifest.yaml
  - PROJECT_CONTEXT/current_status.md
  - PROJECT_CONTEXT/architecture.md
  - USAGE_GUIDES/QUICK_START/codex.md
  - USAGE_GUIDES/QUICK_START/opencode.md
  - actual OpenCode debug output and loading directories
- Modified:
  - PROJECT_CONTEXT/current_status.md
  - PROJECT_CONTEXT/task_ledger.md
  - OpenCode loading entries for `style-doctor` and `zyc`
  - affected generated workspace reports
- Decision:
  - Preserve `${WORKSPACE_ROOT}` as the only skill source.
  - Replace the two identical OpenCode directory copies with junctions to workspace source.
  - Preserve the replaced copies under `${DATA_ROOT}/opencode\projection-backups\20260611-232730` until cleanup is separately approved.
  - Leave `cpp-code-review`, OpenCode CLI, configuration roots, and skill behavior unchanged.
- Validation:
  - Source and pre-change directory copies matched by SHA-256 with zero differences.
  - OpenCode debug output discovered `style-doctor`, `zyc`, and `cpp-code-review`.
  - `scripts/check_links.ps1` reported all five manifest projections OK.
  - Backup copies matched workspace source by SHA-256 after replacement.
- Next:
  - Observe the junction-backed OpenCode skills during normal use.
  - Remove the timestamped backup only after explicit approval and a stable observation period.
  - Continue with the unified developer interface only as a separate flow item.

### TASK-20260611-002 - Enforce required and optional resource failures

- Date: 2026-06-11
- Status: done
- Task type: context_resolution_tooling
- Branch: codex/failure-enforcement-p0
- Commit: 66084d2
- Read:
  - shared/failure_policy.md
  - shared/discovery_rules.md
  - PROJECT_CONTEXT/task_registry.yaml
  - scripts/resolve_task_context.py
  - scripts/tests/test_resolve_task_context.py
- Modified:
  - README.md
  - PROJECT_CONTEXT/task_ledger.md
  - scripts/resolve_task_context.py
  - scripts/tests/test_resolve_task_context.py
- Decision:
  - Treat missing required and preloaded task context as blocking errors.
  - Treat missing optional context as a visible degraded-mode warning only when optional context is expanded.
  - Keep overall task status separate from the pure token-budget status.
  - Treat unresolved required, write-scope, and validation placeholders as blocking instead of guessing paths.
  - Expose structured resource findings for developer and agent integrations.
- Validation:
  - Resolver and startup policy tests passed.
  - Missing required task context returned exit code 1.
  - Valid registered task context returned exit code 0.
  - Optional missing context remained non-blocking.
  - Git whitespace validation passed.
- Next:
  - Restore OpenCode skill loading entries to source-linked projections under P0.2.
  - Add the same required/optional regression contract to future unified developer CLI work.

### TASK-20260611-001 - Add task-level tool policy

- Date: 2026-06-11
- Status: done
- Task type: context_resolution_tooling
- Branch: codex/task-tool-policy
- Commit: c5a3f22
- Read:
  - AGENTS.md
  - PROJECT_CONTEXT/task_registry.yaml
  - PROJECT_CONTEXT/context_budget.md
  - PROJECT_CONTEXT/task_ledger.md latest entries
  - scripts/resolve_task_context.py
  - scripts/tests/test_resolve_task_context.py
- Modified:
  - AGENTS.md
  - PROJECT_CONTEXT/task_registry.yaml
  - PROJECT_CONTEXT/context_budget.md
  - PROJECT_CONTEXT/task_ledger.md
  - scripts/resolve_task_context.py
  - scripts/tests/test_resolve_task_context.py
- Decision:
  - Use portable capability classes rather than platform-specific MCP tool names.
  - Default to `deny_unlisted`.
  - Separate read-only, workspace maintenance, platform maintenance, and cleanup/migration profiles.
  - Require explicit confirmation for commits, pushes, platform writes, environment writes, moves, and deletions according to task profile.
  - Deny browser sessions, email, messaging, office writes, and credential access for current workspace maintenance tasks.
- Validation:
  - Resolver tests cover default, maintenance, and unknown tool profiles.
  - Every registered task resolves to an explicit profile.
- Next:
  - Map the capability contract to host-enforced MCP configuration only when a supported client interface is available.

### TASK-20260610-002 - Compress always-loaded startup context

- Date: 2026-06-10
- Status: done
- Task type: startup_context_optimization
- Branch: codex/startup-context-p5-3
- Commit: pending
- Read:
  - AGENTS.md
  - PROJECT_CONTEXT/task_registry.yaml
  - PROJECT_CONTEXT/context_budget.md
  - PROJECT_CONTEXT/task_ledger.md latest entries
  - scripts/resolve_task_context.py
  - existing resolver tests and task measurements
- Modified:
  - AGENTS.md
  - README.md
  - PROJECT_CONTEXT/task_registry.yaml
  - PROJECT_CONTEXT/context_budget.md
  - PROJECT_CONTEXT/current_status.md
  - PROJECT_CONTEXT/todo.md
  - PROJECT_CONTEXT/task_ledger.md
  - scripts/resolve_task_context.py
  - scripts/tests/test_startup_context_policy.py
- Decision:
  - Keep only startup routing, always-on safety, source boundaries, and knowledge-layer routing in root `AGENTS.md`.
  - Leave protocol validation, migration procedures, skill methodology, and detailed usage instructions to task-resolved context.
  - Enforce a machine-readable root-instruction token ceiling.
  - Deduplicate files already counted as preloaded context from required-file token totals.
- Validation:
  - Root `AGENTS.md` decreased from about 1,375 to 531 heuristic tokens.
  - Resolver and startup policy tests passed.
  - Narrow task budgets remained below their warning threshold.
  - Startup optimization no longer counts `AGENTS.md` twice.
- Next:
  - Collect real task measurements before adjusting thresholds.
  - Consider P5.4 only when file discovery, not startup context, becomes the remaining bottleneck.

### TASK-20260610-001 - Add task resolver and context token meter

- Date: 2026-06-10
- Status: done
- Task type: context_resolution_tooling
- Branch: codex/context-resolver-p5
- Commit: pending
- Read:
  - AGENTS.md
  - PROJECT_CONTEXT/task_registry.yaml
  - PROJECT_CONTEXT/context_budget.md
  - PROJECT_CONTEXT/task_ledger.md latest entries
  - USAGE_GUIDES/prompt_registry.yaml
  - existing workspace Python script conventions
- Modified:
  - scripts/resolve_task_context.py
  - scripts/tests/test_resolve_task_context.py
  - scripts/requirements-context-tools.txt
  - AGENTS.md
  - README.md
  - PROJECT_CONTEXT/task_registry.yaml
  - PROJECT_CONTEXT/context_budget.md
  - PROJECT_CONTEXT/README.md
  - PROJECT_CONTEXT/current_status.md
  - PROJECT_CONTEXT/todo.md
  - PROJECT_CONTEXT/task_ledger.md
- Decision:
  - Resolve one exact task id into required context, prompt guidance, evidence, write scope, validation, and token estimates.
  - Resolve standalone prompt ids and extract only a referenced Markdown anchor section when requested.
  - Consume full task/prompt registries inside the resolver and omit them from model context unless the task maintains them.
  - Keep optional files demand-loaded and measure them only with `--include-optional`.
  - Use warning-first token budgets with optional strict non-zero exit behavior.
  - Use `tiktoken` when installed and a labeled multilingual heuristic fallback otherwise.
- Validation:
  - Eighteen resolver unit tests cover routing, placeholders, consumed registries, evidence separation, path escape, wildcard ignore policy, templates and anchors, optional context, fallback counting, and budget overrides.
  - Typical task resolution and JSON output verified.
- Next:
  - Gather real task measurements before P5.3 startup-context compression.
  - Consider P5.4 lightweight repo map only after resolver usage shows a retrieval gap.

### TASK-20260609-002 - Separate skill contracts from platform exposure

- Date: 2026-06-09
- Status: done
- Task type: skill_architecture_update
- Branch: main
- Commit: pending
- Read:
  - workspace_manifest.yaml
  - PROJECT_CONTEXT startup and architecture files
  - shared role, runtime, path, and portability policies
  - four core skill entry documents
  - manifest-aware bootstrap, validation, migration, link, and report scripts
  - user-facing usage guides and reusable skill-engineering patterns
- Modified:
  - workspace_manifest.yaml
  - AGENTS.md, PROJECT_CONTEXT/, shared/, USAGE_GUIDES/, and SKILL_ENGINEERING/ semantic docs
  - four core skill entry and compatibility docs
  - scripts/bootstrap_workspace.py
  - scripts/validate_manifest.py
  - scripts/migration_dry_run.py
  - scripts/sync_report.ps1
  - current manifest, protocol, migration, setup, and health report snapshots
  - Codex ZYC loading projection at workspace_manifest.yaml -> projections[codex.zyc]
- Decision:
  - Model `role`, `authority`, `execution_modes`, and `exposures[]` independently.
  - Treat platform loading as visibility rather than ownership or permission.
  - Keep legacy `platform` and `projection_path` fields synchronized with the first exposure during migration.
  - Expose the existing ZYC source to both OpenCode and Codex without copying source files.
  - Keep legacy `generate_opencode_skill` accepted as a no-op while removing it from new-config guidance.
- Validation:
  - Manifest validation: 0 errors, 0 warnings.
  - Protocol validation: 0 errors, 1 expected lightweight-schema warning.
  - All five manifest projections passed link validation.
  - OpenCode discovery lists `style-doctor` and `zyc`.
  - Codex ZYC junction and `SKILL.md` frontmatter were verified; desktop refresh/restart is still required for UI discovery confirmation.
  - Character-generator unit tests: 9 passed.
  - Migration dry-run verified multi-exposure behavior for a Codex root change.
  - `sync_report.ps1` reduced from timeout to about 4 seconds by scanning Git-visible text files instead of the `.git` object store.
- Next:
  - Refresh Codex Desktop and confirm `zyc` appears in the skill picker.
  - Retire legacy single-platform manifest fields only after all consumers read `exposures[]`.

### TASK-20260609-001 - Add lightweight execution capability modes

- Date: 2026-06-09
- Status: done
- Task type: default rules (execution capability guard)
- Branch: main
- Commit: pending
- Read:
  - workspace_manifest.yaml
  - PROJECT_CONTEXT/task_registry.yaml
  - PROJECT_CONTEXT/context_budget.md
  - PROJECT_CONTEXT/task_ledger.md latest entries
  - shared/workspace_policy.md
  - shared/failure_policy.md
  - shared/patch_protocol.md
  - four core skill SKILL.md and SHARED_PROTOCOLS.md files
- Modified:
  - shared/workspace_policy.md
  - codex/character-generator/SKILL.md
  - codex/character-maintainer/SKILL.md
  - opencode/style-doctor/SKILL.md
  - opencode/characters/zyc/SKILL.md
  - PROJECT_CONTEXT/task_ledger.md
- Decision:
  - Define `text_only`, `record_write`, and `source_patch` as lightweight execution modes.
  - Default all four skills to `text_only` and require explicit scope plus verifiable workspace capabilities before write escalation.
  - Keep ZYC text-only, prohibit source patches from style-doctor, and preserve existing generator/maintainer authority boundaries.
  - Do not add automatic capability negotiation, model scoring, schema enforcement, or a compatibility test matrix in this pass.
- Validation:
  - All four core skills passed `quick_validate.py` (ZYC validated with UTF-8 mode).
  - `python scripts/validate_protocols.py` completed with 0 errors and 2 warnings.
  - The warnings cover lightweight schema enforcement and the pre-run stale report snapshot; neither expands skill authority.
  - Focused diff confirmed that `style-doctor` cannot enter `source_patch` and ZYC remains `text_only`.
- Next:
  - Add deeper capability negotiation only after cross-model evidence shows the lightweight declarations are insufficient.

### TASK-20260601-004 - Deduplicate source-of-truth path facts

- Date: 2026-06-01
- Status: done
- Task type: source_of_truth_dedup
- Branch: codex/task-registry-p0
- Commit: pending
- Read:
  - workspace_manifest.yaml
  - PROJECT_CONTEXT/current_status.md
  - PROJECT_CONTEXT/architecture.md
  - PROJECT_CONTEXT/session_handoff.md
  - PROJECT_CONTEXT/decisions.md
  - PROJECT_CONTEXT/glossary.md
  - USAGE_GUIDES/QUICK_START/
  - USAGE_GUIDES/PROMPT_TEMPLATES/
  - USAGE_GUIDES/prompt_registry.yaml
  - shared/future_drift_policy.md
- Modified:
  - PROJECT_CONTEXT/current_status.md
  - PROJECT_CONTEXT/architecture.md
  - PROJECT_CONTEXT/session_handoff.md
  - PROJECT_CONTEXT/decisions.md
  - PROJECT_CONTEXT/glossary.md
  - PROJECT_CONTEXT/bugs.md
  - PROJECT_CONTEXT/experiment_log.md
  - PROJECT_CONTEXT/todo.md
  - PROJECT_CONTEXT/task_registry.yaml
  - PROJECT_CONTEXT/task_ledger.md
  - USAGE_GUIDES/SAFETY.md
  - USAGE_GUIDES/QUICK_START/
  - USAGE_GUIDES/PROMPT_TEMPLATES/
  - USAGE_GUIDES/REFERENCE/codex/character-generator.md
  - USAGE_GUIDES/prompt_registry.yaml
  - shared/future_drift_policy.md
- Decision:
  - Keep current local source root, platform root, and projection path facts centralized in `workspace_manifest.yaml`.
  - Replace duplicated current path facts in context and usage docs with manifest field references.
  - Use `<workspace-root>` placeholders in copy-ready prompt examples.
  - Leave report snapshots untouched unless a separate report regeneration task is opened.
- Validation:
  - Non-report context and usage layers no longer contain the searched local absolute path facts.
  - `USAGE_GUIDES/prompt_registry.yaml` parsed successfully as YAML.
  - All task prompt ids in `PROJECT_CONTEXT/task_registry.yaml` exist in `USAGE_GUIDES/prompt_registry.yaml`.
  - All template paths declared in `USAGE_GUIDES/prompt_registry.yaml` exist.
  - `python scripts/validate_protocols.py` completed with 0 errors and 2 warnings.
  - `git diff --check` passed; Git still reports the known CRLF warning for the regenerated protocol validation report.
- Next:
  - Review P4 changes.
  - Commit P4 if accepted.

### TASK-20260601-003 - Establish prompt registry

- Date: 2026-06-01
- Status: done
- Task type: prompt_usage_update
- Branch: codex/task-registry-p0
- Commit: 65eab52
- Read:
  - USAGE_GUIDES/README.md
  - USAGE_GUIDES/START_HERE.md
  - USAGE_GUIDES/PROMPT_TEMPLATES/README.md
  - PROJECT_CONTEXT/task_registry.yaml
  - PROJECT_CONTEXT/task_ledger.md latest entries
- Modified:
  - USAGE_GUIDES/prompt_registry.yaml
  - USAGE_GUIDES/README.md
  - USAGE_GUIDES/START_HERE.md
  - USAGE_GUIDES/PROMPT_TEMPLATES/README.md
  - PROJECT_CONTEXT/task_registry.yaml
  - PROJECT_CONTEXT/context_budget.md
  - PROJECT_CONTEXT/current_status.md
  - PROJECT_CONTEXT/todo.md
  - PROJECT_CONTEXT/task_ledger.md
- Decision:
  - Add `USAGE_GUIDES/prompt_registry.yaml` as the P3 prompt id registry.
  - Map task prompt ids such as `minimal_edit`, `platform_exposure`, and `drift_repair` to reusable prompt frames.
  - Register existing copy-ready templates by path instead of duplicating their full content.
- Validation:
  - `USAGE_GUIDES/prompt_registry.yaml` parsed successfully as YAML.
  - All task prompt ids in `PROJECT_CONTEXT/task_registry.yaml` exist in `USAGE_GUIDES/prompt_registry.yaml`.
  - All template paths declared in `USAGE_GUIDES/prompt_registry.yaml` exist.
  - `git diff --check` passed.
- Next:
  - Consider dedicated long-form template files only when prompt frames outgrow the registry.

### TASK-20260601-002 - Establish task ledger

- Date: 2026-06-01
- Status: done
- Task type: task_registry_update
- Branch: codex/task-registry-p0
- Commit: 2e03532
- Read:
  - AGENTS.md
  - PROJECT_CONTEXT/task_registry.yaml
  - PROJECT_CONTEXT/context_budget.md
  - PROJECT_CONTEXT/README.md
  - PROJECT_CONTEXT/current_status.md
  - PROJECT_CONTEXT/todo.md
- Modified:
  - PROJECT_CONTEXT/task_ledger.md
  - PROJECT_CONTEXT/task_registry.yaml
  - PROJECT_CONTEXT/context_budget.md
  - PROJECT_CONTEXT/README.md
  - PROJECT_CONTEXT/current_status.md
  - PROJECT_CONTEXT/todo.md
  - AGENTS.md
- Decision:
  - Add this ledger as the P2 continuity layer.
  - Future sessions should read only the latest 5 entries unless evidence requires older history.
  - The ledger records maintenance decisions; it does not replace manifest, shared protocols, reports, or Git.
- Validation:
  - `PROJECT_CONTEXT/task_registry.yaml` parsed successfully as YAML.
  - `git diff --check` passed.
- Next:
  - Continue to P3 Prompt Registry.

### TASK-20260601-001 - Establish task registry and context budget

- Date: 2026-06-01
- Status: done
- Task type: task_registry_update
- Branch: codex/task-registry-p0
- Commit: 376ddbd
- Read:
  - AGENTS.md
  - PROJECT_CONTEXT/README.md
  - PROJECT_CONTEXT/current_status.md
  - PROJECT_CONTEXT/todo.md
  - workspace_manifest.yaml
  - .gitignore
- Modified:
  - PROJECT_CONTEXT/task_registry.yaml
  - PROJECT_CONTEXT/context_budget.md
  - PROJECT_CONTEXT/README.md
  - PROJECT_CONTEXT/current_status.md
  - PROJECT_CONTEXT/todo.md
  - AGENTS.md
- Decision:
  - P0 established `PROJECT_CONTEXT/task_registry.yaml` as the task routing layer.
  - P1 established `PROJECT_CONTEXT/context_budget.md` as the context expansion budget.
  - Maintenance should classify the task before broad discovery, then load required context before optional context.
- Validation:
  - P1 committed as `376ddbd Add P1 context budget for task routing`.
- Next:
  - P2 should add a durable, lightweight ledger for continuity.
