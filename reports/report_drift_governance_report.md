---
report_name: report_drift_governance_report
generated_at: 2026-05-27 22:15:00 +08:00
generated_by: documentation reliability audit
source_root: ${WORKSPACE_ROOT}
manifest_path: ${WORKSPACE_ROOT}\workspace_manifest.yaml
manifest_version: 1.0.0
manifest_last_modified: 2026-05-26 22:36:48 +08:00
source_commit: 7099172
report_scope: report snapshot policy, future drift policy, and core skill cooperation boundaries
report_is_snapshot: true
truth_source:
  - workspace_manifest.yaml
  - shared/
  - current git commit
staleness_policy: Regenerate after manifest, shared policy, report generation, Git baseline, or cooperation boundary changes.
---

Report is a snapshot. Manifest is the source of truth. If this report conflicts with the manifest, trust the manifest and regenerate the report.

# Report Drift Governance Report

## Modified Files

- `shared/reporting_policy.md`
- `shared/future_drift_policy.md`
- `shared/workspace_policy.md`
- `shared/workspace_path_policy.md`
- `shared/versioning_policy.md`
- `scripts/sync_report.ps1`
- `reports/workspace_setup_report.md`
- `reports/workspace_health_report.md`
- `reports/git_governance_report.md`
- `codex/character-generator/README.md`
- `codex/character-generator/SKILL.md`
- `codex/character-generator/SHARED_PROTOCOLS.md`
- `codex/character-generator/AGENTS.md`
- `codex/character-maintainer/README.md`
- `codex/character-maintainer/SKILL.md`
- `codex/character-maintainer/SHARED_PROTOCOLS.md`
- `opencode/style-doctor/README.md`
- `opencode/style-doctor/SKILL.md`
- `opencode/style-doctor/SHARED_PROTOCOLS.md`
- `opencode/characters/zyc/README.md`
- `opencode/characters/zyc/SKILL.md`
- `opencode/characters/zyc/SHARED_PROTOCOLS.md`
- `reports/report_drift_governance_report.md`

## Why These Changes Were Made

The workspace had functional reports, but their authority model was implicit. This can cause report drift: old generated observations can be mistaken for source-of-truth after manifest, shared policy, Git, or projection changes.

The changes make reports explicitly snapshot-based and document future drift ownership without changing skill runtime behavior.

## Reports Drift Protection

Reports now follow these rules:

- Reports are snapshots.
- `workspace_manifest.yaml`, `shared/`, and the current Git commit are truth sources.
- If a report conflicts with manifest, trust manifest and regenerate the report.
- Important reports should include `generated_at`, `generated_by`, `source_root`, `manifest_path`, `manifest_version`, `manifest_last_modified`, `source_commit`, `report_scope`, and `report_is_snapshot: true`.

`sync_report.ps1` now writes this header for:

- `reports/workspace_setup_report.md`
- `reports/workspace_health_report.md`

`reports/git_governance_report.md` was updated with an equivalent historical snapshot header.

## Future Drift Protection

`shared/future_drift_policy.md` defines drift risk and ownership for:

- style-doctor taxonomy drift
- ZYC manual evolution drift
- reports drift
- platform/source confusion
- manifest/link drift

Key rules:

- New drift vocabulary starts in `shared/drift_taxonomy.md`.
- ZYC-specific evolution is not automatically promoted to generator templates.
- `character-maintainer` classifies lessons as generalizable, character-specific, or uncertain.
- Platform directories remain projection surfaces.
- Link state is checked through `scripts/check_links.ps1`.

## Skill Cooperation Updates

Small cooperation notes were added:

- `character-generator`: batch production and generation workflow, not mature character maintenance.
- `character-maintainer`: long-term character evolution and generalizable-vs-specific classification, not direct generator editing.
- `style-doctor`: runtime diagnosis and patch suggestion, taxonomy aligned with shared drift taxonomy.
- `zyc`: manually evolved character skill; repeated runtime drift should go through style-doctor then maintainer.

## Files That May Still Become Stale

- `reports/git_governance_report.md`: historical report; supersede after future Git governance work.
- `reports/workspace_setup_report.md`: regenerate after manifest or projection changes.
- `reports/workspace_health_report.md`: regenerate after manifest, shared policy, projection, Git baseline, or report script changes.
- Per-character reports under character folders: follow each character's privacy and Git policy.

## Not Handled In This Pass

- `.git.disabled-*` cleanup was not touched.
- CRLF warnings were not addressed.
- Runtime loop durable behavior was not changed.
- Shared schema or validators were not added.
- Manifest portability was not redesigned.
- Junctions and platform projections were not rebuilt.
- Skill core behavior and prompt logic were not changed.

## Next Recommendations

1. Review these documentation-only changes.
2. Run `scripts/check_links.ps1` before any future projection changes.
3. Regenerate setup/health reports with `scripts/sync_report.ps1` after manifest or shared policy changes.
4. Commit this pass if the policy wording matches the intended governance model.
