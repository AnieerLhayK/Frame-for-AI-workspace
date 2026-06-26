---
report_name: manifest_portability_report
generated_at: 2026-05-28 00:43:06 +08:00
generated_by: Codex
source_root: ${WORKSPACE_ROOT}
manifest_path: ${WORKSPACE_ROOT}\workspace_manifest.yaml
source_commit: c600823
report_scope: manifest portability and bootstrap discovery setup
report_is_snapshot: true
truth_source:
  - workspace_manifest.yaml
  - shared/
  - current git commit
---

Report is a snapshot. Manifest is the source of truth. If this report conflicts with the manifest, trust the manifest and regenerate the report.

# Manifest Portability Report

## 1. Current Manifest Portability Status

The workspace now has explicit portability metadata in `workspace_manifest.yaml`:

- bounded bootstrap discovery is enabled;
- internal paths are declared as workspace-relative;
- platform roots and projection links remain absolute local deployment paths;
- migration dry-run is supported;
- automatic file moves and automatic relinking are not allowed.

Manifest validation currently reports `0` errors and `0` warnings.

## 2. New Scripts

- `scripts/bootstrap_workspace.py`
- `scripts/validate_manifest.py`
- `scripts/migration_dry_run.py`

These scripts do not move files, copy shared protocols, or rebuild links.

## 3. Bootstrap Discovery

`bootstrap_workspace.py` starts from a provided path, walks upward looking for `workspace_manifest.yaml`, and stops at the configured parent depth. It reports the workspace root, manifest path, shared root, platform roots, and source-of-truth value.

It does not scan whole drives, guess historical paths, or silently fall back to projections.

## 4. Manifest Validation

`validate_manifest.py` checks that the manifest exists, parses, includes required sections, resolves declared source paths, resolves shared protocols, verifies projection targets against source paths, and reports explained absolute path fields.

Critical missing manifest structure or required source paths fail with a non-zero exit code. Portability observations remain warnings.

## 5. Migration Dry-Run

`migration_dry_run.py` simulates path changes without changing the filesystem.

Supported scenarios include:

- `root-rename`
- `drive-change`
- `shared-move`
- `codex-root-change`
- `opencode-root-change`

The dry-run report lists affected manifest fields, projections, scripts, reports, skill docs, manual steps, risks, and rollback advice.

## 6. Absolute Paths Still Kept

The manifest still keeps these absolute paths:

- `workspace.source_of_truth`
- `platform_roots.codex`
- `platform_roots.opencode`
- `skills[].projection_path`
- `projections[].link_path`
- `shared.projection_paths.*`

They remain because they describe current-machine deployment and platform entry points. Centralizing them in the manifest is intentional; spreading them into skill docs is not.

## 7. Future Relative Candidates

Future manifest versions could derive these from `platform_roots`:

- `skills[].projection_path`
- `projections[].link_path`
- `shared.projection_paths.*`

That should wait until scripts support templated platform projections without ambiguity.

## 8. Not Moved

This task did not move:

- `${WORKSPACE_ROOT}`
- `D:\skills_codex`
- `D:\opencode\.opencode\skills`
- `shared/`
- any skill directory

## 9. Not Rebuilt

This task did not rebuild, remove, or recreate junctions or symlinks.

`scripts/check_links.ps1` was run only as validation.

## 10. Current Risks

- Reports still contain historical absolute paths as snapshots.
- Platform tools may rely on absolute projection roots.
- A future shared move would require protocol path review, not only manifest edits.
- PowerShell scripts now include bounded discovery logic, but Python remains the reference bootstrap implementation.

## 11. Next Stage Recommendations

- Add automated tests for the three portability scripts.
- Consider deriving projection link paths from `platform_roots` in a future manifest format.
- Add stale-report detection for manifest validation and migration dry-run reports.
- Keep running `validate_manifest.py`, `validate_protocols.py`, and `check_links.ps1` before path migrations.
