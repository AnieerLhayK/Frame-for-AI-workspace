# Manifest Portability Policy

This policy defines how the workspace should remain recoverable when local directories, drive letters, or platform projection roots change.

## Local Absolute Paths Are Allowed In Manifest

`workspace_manifest.yaml` may contain local absolute paths for:

- `workspace.source_of_truth`
- `platform_roots`
- platform projection link paths
- shared projection paths
- external Claude Code and OpenCode session-store roots

These paths describe the current machine deployment. They should remain centralized in the manifest and should not spread back into skill docs or source files.

## Prefer Workspace-Relative Internal Paths

Workspace-internal source paths should be workspace-relative whenever possible:

- `shared.source_path`
- `packages[].source_path`
- `packages[].runtime_path`
- `packages[].engineering_path`
- `packages[].shared_path`
- `packages[].reports_path`
- `packages[].protocol_manifest`
- `skills[].source_path`
- `skills[].package_id`
- `skills[].protocol_dependencies`
- `skills[].exposures[].projection_id`
- `projections[].target_path`
- `protocols[].path`
- required and optional skill file paths

This keeps source layout portable even when the workspace root changes.

## Bootstrap Discovery

`workspace.source_of_truth` should be explainable by bounded bootstrap discovery. Tools should find `workspace_manifest.yaml` by walking upward from a provided start directory with a maximum parent depth, not by scanning an entire drive.

Use:

```powershell
python scripts\bootstrap_workspace.py
```

## Projection Paths Are Deployment Data

Projection paths are local deployment compatibility surfaces for Codex and OpenCode. They are not portable source layout. A moved workspace may require intentionally updating projection roots and recreating links after review.

`skills[].platform` and `skills[].projection_path` are compatibility aliases for the first exposure during the manifest 1.x migration. New readers should prefer `skills[].exposures[]` and resolve paths through `projections[]`.

## Protocol Resolution

Resolve workspace governance through:

```text
workspace_manifest.yaml -> shared.source_path
```

Resolve domain protocols through:

```text
workspace_manifest.yaml -> skills[].package_id
workspace_manifest.yaml -> packages[].shared_path
workspace_manifest.yaml -> packages[].protocol_manifest
```

Prefer workspace-relative protocol paths. Platform projections are discovery
surfaces, not replacement protocol sources.

## Migration Checks

Before migrating directories, run:

```powershell
python scripts\bootstrap_workspace.py
python scripts\validate_manifest.py
python scripts\migration_dry_run.py --scenario root-rename --new-root <new-workspace-root>
python scripts\validate_protocols.py
powershell -ExecutionPolicy Bypass -File scripts\check_links.ps1
```

## Manifest Maintenance

The manifest is the source of truth, but it is not a magic file that never
changes. If the workspace root, package paths, shared roots, or platform roots
intentionally move, update the manifest and rerun validation.

Reports may contain old paths as snapshots. If reports conflict with the manifest, trust the manifest and regenerate reports.

Source moves must also follow `shared/session_continuity_policy.md`. Session
stores stay outside the Git tree, and old working-directory values may remain as
historical metadata when project identity is unchanged.
