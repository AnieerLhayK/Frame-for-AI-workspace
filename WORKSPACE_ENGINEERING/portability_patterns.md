# Portability Patterns

Portability work makes a workspace recoverable after local paths change.

## Avoid Scattered Hardcoded Paths

Hardcoded paths in many files make migration expensive. Centralizing them in the manifest is already a major improvement.

## Central Absolute Paths Are Better Than Scattered Absolute Paths

Some platform roots are genuinely local. Keeping those values in one manifest lets tools reason about them and lets reports identify what must change.

## Workspace-Relative Internal Paths

Internal source paths should be workspace-relative when possible. This lets the workspace move without rewriting every skill document.

## Bounded Bootstrap Discovery

Bootstrap discovery should start from a known path and walk upward with a max depth. It should not scan whole drives or guess silently.

## Migration Dry-Run

Dry-run reports reveal affected manifest fields, projections, reports, scripts, docs, risks, and manual steps before any file movement.

## Portability And Safety Tradeoff

More automation is not always safer. Automatic movement, copying, or relinking can damage a workspace faster than a clear dry-run plus manual confirmation.

## Good Migration Sequence

```text
bootstrap -> validate manifest -> migration dry-run -> validate protocols -> check links -> explicit human migration decision
```

---

## Patterns From Experience

### Claude Code Handoff Compatibility

When adding Claude Code as a new platform (2026-06-13), the workspace needed compatibility without changing its architecture:

1. Root `CLAUDE.md` imports `AGENTS.md` via `@AGENTS.md` — no policy duplication.
2. `.claude/project-boundary.json` declares allowed workspace layers.
3. `.claude/hooks/workspace_boundary_guard.ps1` prevents writes outside allowed layers.
4. `.claude/rules/workspace-boundary.md` reminds agents to resolve tasks before broad discovery.

The key insight: **Claude Code treats startup CWD as the project selector**. The workspace does not register Claude Code in `workspace_manifest.yaml`; instead, `project_roots.json` maps launcher aliases (`claude-workspace`, `claude-cnn`) to separate Git roots. This keeps the manifest as a skill registry rather than an external-project registry.

### Cross-Platform Path Detection

The change surface planner (`scripts/plan_change_surface.py`) must handle three absolute path formats on one host:

| Format | Example |
| ------ | ------- |
| Windows drive | `C:\workspace` |
| Windows UNC | `\\server\share` |
| POSIX | `/mnt/d/workspace` |

The planner detects each format independently of the host OS. It classifies all absolute paths as `external_or_projection` (blocked as source edit targets) while keeping repository-relative paths in their source-layer classification. Cross-platform path tests should accompany every path rule change.

### Machine-Local Paths Belong In The Manifest

The manifest still contains local absolute paths (`workspace.source_of_truth`, `platform_roots.*`). This is intentional — they are deployment metadata, not portability flaws. The portability guarantees come from:

- `scripts/bootstrap_workspace.py` (bounded discovery, no drive scans)
- `scripts/validate_manifest.py` (structural checks)
- `scripts/migration_dry_run.py` (what changes before a move)
- `shared/manifest_portability_policy.md` (rules for safe migration)

The dry-run scenario (`--scenario root-rename`) reveals exactly which manifest fields, projections, reports, scripts, docs, and manual steps are affected before any files move.
