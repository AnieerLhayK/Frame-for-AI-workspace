# Governance Patterns

Governance is useful when it protects flexibility instead of replacing it.

## Git Baseline

Establishing a baseline before governance work makes every later structural change reviewable.

## Source-Of-Truth

Name the authority for each class of fact. Paths belong to the manifest; protocols belong to `shared/`; reports are snapshots; skill behavior belongs to source files.

## Validator

Validators should catch core drift with low noise. Required missing files should be errors; optional missing files should be warnings.

## Reports Governance

Reports need scope and timestamp headers. A report without context can mislead future agents.

## Protocol Contracts

Protocol manifests turn shared docs from informal agreements into checkable contracts.

## Snapshot Policy

Snapshot reports should say they are snapshots. They should never claim to be stronger than current source state.

## Failure Policy

Failure policy should distinguish critical missing, optional missing, and degraded mode. This prevents both panic and silent drift.

## Required vs Optional

Required artifacts are needed for correct operation. Optional artifacts may improve completeness but should not block normal maintenance.

## Portability Governance

Portability is not path removal. It is the ability to explain, validate, and dry-run path changes before they happen.

---

## Patterns From Experience

### Task Registry As Context Gate

The task registry (`PROJECT_CONTEXT/task_registry.yaml`) prevents broad context loading before work begins:

```yaml
- id: startup_context_optimization
  use_when: reduce startup context size
  required: [project context root files]
  optional: [older ledger entries]
  tool_profile: limited
```

Before the registry, the first route consumed ~15k tokens. After declaring optional context and limiting preloaded files, the same route dropped to ~5k tokens and `PASS`.

Key design: the registry does not duplicate file content — it routes which files to load. The resolver joins the registry, prompt registry, and budget without writing files.

### PreToolUse Write Guard

A PowerShell boundary guard (`.claude/hooks/workspace_boundary_guard.ps1`) intercepts Write/Edit/Bash tools and validates each target path against `project-boundary.json`:

- Allows writes within `allowed_top_level` directories and `allowed_root_files`.
- Blocks writes to `claude/`, external repositories, and unregistered paths.
- Mutating Bash commands are checked for drive-letter paths; paths outside allowed layers are denied.

This is read-only policy enforcement — the guard reads `project-boundary.json` at each invocation, so updates to the policy take effect immediately without hook redeployment.

### Context Budget Layering

The context budget (`PROJECT_CONTEXT/context_budget.md`) defines escalation levels:

1. Resolver output (always loaded)
2. Required context (loaded on task resolve)
3. Optional context (loaded only from evidence)
4. Full context (loaded only when explicitly needed)

Each level has a token ceiling with per-task overrides. Missing required context is an ERROR; missing optional is a WARNING.

### Knowledge Registry As Topic Index

Instead of loading all knowledge files upfront, the knowledge registry (`.yaml`) indexes topics and returns paths before loading content. Chinese aliases let the user search in their normal vocabulary.

The constraint: do not turn the registry into copied documentation. It is a routing index pointing to the correct file.

### Lightweight Knowledge Routing

Added at the end of this governance pass (2026-06-13): a five-question exit
check that routes reusable experiences to the engineering knowledge base:

- Is there a reusable pattern?
- Is there a new anti-pattern?
- Is there a real incident case?
- Is there an experiment conclusion?
- Has the risk profile changed?

If all five answer NO, the experience stays in the task ledger and Git history. This prevents documentation noise while ensuring important lessons don't stay buried.

### Registration Is A Contract, Not Authentication

An Agent registry can declare reviewed identity, lifecycle, Role, scope,
platform references, and storage boundaries. It cannot prove that the current
process is genuinely that Agent.

Use registration to resolve policy and fail closed. Use platform-supported
authentication or attestation when strong caller identity is required.

### Invalid Registration Must Degrade Safely

Registration parsers should never fill missing trust, Role, or scope fields with
privileged defaults. Unknown, incomplete, proposed, suspended, and retired
registrations should resolve to a useful Consumer mode that permits reading,
explicit Skill invocation, and reviewable requests without source mutation.

### Git Diff Is Runtime Governance Evidence

Declared scope is an intention. The Git worktree is evidence of what actually
happened. Post-change verification should compare unstaged, staged, and
untracked paths with the task's resolved `write_scope`.

High-permission maintainers still need path boundaries. A maintainer may edit a
high-risk governance file when the task declares it, but broad authority should
not excuse unrelated changes.

### Preserve Out-Of-Scope Work

A scope verifier should detect and stop expansion, not punish the worktree.
Never respond to an out-of-scope result with automatic reset, checkout, clean,
deletion, or overwrite. Preserve the result and choose a better task, a safety
branch, manual selection, or a high-risk worktree.

### Worktrees Are Risk Isolation

Use worktrees for concurrent work, destructive migration, Skill moves/deletes,
and temporary structural authority. Ordinary scoped source edits,
documentation, and report refreshes do not need a worktree merely because
governance exists.

### Unified Change Risk

Risk classification should reuse the same surface model that already governs
agent writes. Keep machine-readable path patterns and operation triggers in one
policy, then let task `write_scope` answer whether the current task declared
the affected path.

Use only three output levels:

- `normal`: ordinary scoped work;
- `elevated`: an always-on boundary deserves attention;
- `high`: governance, execution-boundary, projection, deletion, or migration
  work needs explicit review.

High permission does not remove path accountability. It allows a capable
maintainer to perform declared high-risk work with tests and review.

### Daily Maintenance Workflow

The ordinary sequence is:

1. resolve;
2. plan only when multiple file sets are plausible;
3. edit;
4. verify actual Git paths;
5. run routed validation;
6. inspect the diff;
7. commit.

`workspace workflow check <task-id>` compresses the read-only post-edit checks.
It verifies scope, checks whitespace in unstaged and staged diffs, and lists
the task's validation commands. It deliberately does not run every test or
perform Git writes.

### Governance Reduction Requires Evidence

Observe 5 to 10 real maintenance tasks before deleting governance. Record
exceptions, false positives, blocked legitimate work, prevented pollution, and
rules that repeatedly fail to affect decisions. Ordinary PASS results need no
new report.

At the end of the observation window, remove or merge only mechanisms whose
lack of decision value is supported by repeated evidence. A verifier should
detect and preserve; it should never turn governance reduction into automatic
punishment or cleanup.

### Memory Is Guidance, Hooks Are Authority

`CLAUDE.md`, `AGENTS.md`, Skill instructions, and injected memory help a model
choose the right action. They do not prevent a weak or distracted model from
calling a write tool.

For any Agent with mutation tools, use two layers:

1. a compact cognitive layer that states Role, allowed records, and handoff
   routes;
2. a tool-dispatch guard that resolves the target and blocks unauthorized
   operations before mutation.

The effective decision is the intersection of task scope, Agent capability,
Agent path scope, acting-Skill execution mode, lease scope, and platform tool
boundary. Never let a permissive task route cancel a denied identity or Skill
decision.

Direct junction exposure needs special care because a write to a platform
loading path can immediately mutate source-of-truth. Resolve links before
authorization, and treat projection visibility as read access unless explicit
deployment authority exists.

Do not attempt to prove arbitrary shell commands harmless with a few string
patterns. For a record-producing Agent, allow a small read-only command set and
route legitimate writes through path-aware file tools. For multiplexed MCP
tools, classify the requested action and fail closed when a mutating action
does not expose a resolvable target path.

### One Authority Model, Platform-Specific Adapters

Do not make Hermes, OpenCode, Reasonix, or future clients invent separate
workspace roles. Give equivalent agents the same registry role and path scopes,
then adapt enforcement to the strongest boundary each platform exposes:

- lifecycle hooks when tool dispatch can be intercepted;
- project permissions when the client merges repository-local configuration;
- bounded native sandboxes and MCP roots as an outer filesystem limit;
- the shared `workspace agent check` decision whenever target paths and acting
  Skill identity are available.

The cognitive prompt is deliberately redundant but not authoritative. It
should remove the model's temptation to bargain for a direct patch: user
approval does not expand the agent's registered role, and a denied agent should
create a diagnosis, handoff, or change request instead of offering to edit.

Project-local adapters keep this governance scoped to the workspace. Running
the same tool in another repository uses that repository's configuration and
is not governed by this workspace merely because the executable is shared.

An untested host such as Cursor should remain a proposed Consumer. Default
registration is not a reason to grant write authority before a real adapter
and bounded experiment exist.

### Migration Must Preserve Read Dependencies

Moving a Skill into a package can preserve every source file while still
breaking the Skill at runtime. Platform Skill loaders commonly confine
`skill_view` to the exposed Skill directory, so references to package-shared
policies, templates, ledgers, or schemas may become unreadable after migration.

Do not solve this by copying shared contracts into each Skill. Keep the package
as source-of-truth and expose only the required shared and record roots through
a read-only platform interface. Health checks should verify both sides of the
contract: mutation tools remain excluded, and required read roots remain
present. A missing read surface is platform exposure drift, not missing source.

### Change Surface Planning

The change surface planner (`scripts/plan_change_surface.py`) compares named alternative file sets against resolved task authority before any edit:

1. Resolve task → get write scope
2. Express intent → `--intent metadata` vs `--intent tooling`
3. Compare options → `--option source=skills/... --option routing=PROJECT_CONTEXT/...`
4. Planner ranks by ownership match, blocks projection paths and report-only targets

The planner is read-only — it produces recommendations, not mutations.
