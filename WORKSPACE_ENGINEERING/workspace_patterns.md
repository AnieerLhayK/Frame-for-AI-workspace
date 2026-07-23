# Workspace Patterns

This file records reusable workspace structure lessons from the current skill ecosystem.

## `packages/`

Domain package layer for related skills. A package may separate runtime,
engineering, shared protocols, and reports without tying source ownership to a
platform.

## `skills/`

Standalone source layer for unrelated skills that share workspace governance
but do not yet need a domain package.

## `shared/`

Workspace-wide protocol layer. It should hold cross-cutting governance, not every domain-specific rule.

Package-specific business and runtime protocols belong under
`packages/<package-id>/shared/`.

## `reports/`

Snapshot layer. It records generated or authored state at a point in time.

## `packages/character-system/reports/runtime-loop/`

Runtime event tracking layer. It records diagnosis, handoff, patches, validation, generalization backlog, and ledgers.

## `PROJECT_CONTEXT/`

Current workspace memory. It answers "what is this project, what happened, and what should the next session read?"

## `WORKSPACE_ENGINEERING/`

Cross-project engineering knowledge. It answers "what have we learned about
building and governing AI workspaces?" Skill-specific methodology belongs in
`WORKSPACE_ENGINEERING/skill_engineering/`.

## `scripts/`

Validation, bootstrap, portability, link, and report automation. Scripts should prefer dry-run, clear errors, and standard libraries.

## Platform Projection

Platform projection roots expose skills to runtime systems. They should remain deployment surfaces, not source ownership boundaries.

One source skill may have multiple projections. Keep role and authority attached to the source contract, not duplicated per platform.

---

## Patterns From Experience

### Source vs Projection Separation In Practice

The workspace maintains one Git root as the single source of truth. Platform loading surfaces declared by `workspace_manifest.yaml -> platform_roots.*` are projection surfaces that junction or symlink back to workspace source directories.

Key rules demonstrated in practice:

- **Git is operated from the workspace root**, never from a projection directory.
- **Projection content is a deployment concern**, not a source. If a projection file differs from source, the source wins.
- **Backups** of replaced projection content may be preserved under a machine-local backup root, but they are not authoritative.
- **Projection backups are read-only archives** — they document what was replaced, not what should be restored.

### Context Resolver As Single Entry Point

The resolver (`scripts/resolve_task_context.py`) unifies three registries into one bounded task view:

```text
tasks/registry/index.yaml → what files to read + tool profile + scope
prompt_registry.yaml  →  what prompts to load + anchors
context_budget.md     →  token ceiling per level
```

The resolver never writes files. It emits a JSON or text response with the task's required context, optional context, write scope, validation commands, and token budget. This prevents each maintenance session from independently guessing which files to read.

### Report Freshness Tracking

Reports are snapshots with embedded timestamps. The report status checker compares each report's generation time against its source dependencies:

- `STRICT` mode: all required report groups must be `FRESH` or the check fails.
- Warnings surface stale reports without blocking normal maintenance.
- `reports refresh` is an explicit command — reports are never regenerated automatically by a read-only check.

### Bootstrap Discovery Protocol

The workspace bootstrap (`scripts/bootstrap_workspace.py`) uses bounded discovery:

1. Start from a known path (workspace root or a declared start path).
2. Walk up at most N levels (default: 10).
3. Find `workspace_manifest.yaml` to confirm identity.
4. Fail with clear error if not found — no silent fallback to guessed paths.
5. No drive-wide scans, no `os.walk("/")`, no heuristic matching.

### PROJECT_CONTEXT Disassembly Pattern

After the initial build-out, PROJECT_CONTEXT accumulated both active (task_ledger, 23 commits) and dormant (bugs.md, 1 commit) files. The fix (2026-06-13):

- **DELETE** what is superseded (bugs → runtime loop diagnosis; experiment_log → task_ledger covers it).
- **MERGE** what has a better home (architecture → root `ARCHITECTURE.md`;
  coding style → `WORKSPACE_ENGINEERING/skill_engineering/style_alignment.md`;
  protocols → `shared/INDEX.md`).
- **KEEP** what is actively used (task ledger, task registry domain index, current status, todo, session handoff).

The principle: a directory that once served as catch-all must have its files
rehomed as the workspace matures, or it becomes stale technical debt. The
promotion from `SKILL_ENGINEERING/` to `WORKSPACE_ENGINEERING/` is itself an
example: the knowledge scope expanded, so Skill Engineering became a named
subdomain instead of remaining an increasingly inaccurate top-level label.
