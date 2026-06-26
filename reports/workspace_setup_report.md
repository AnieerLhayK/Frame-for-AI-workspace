---
report_name: workspace_setup_report
generated_at: 2026-06-25 22:07:45 +08:00
generated_by: scripts/sync_report.ps1
source_root: ${WORKSPACE_ROOT}
manifest_path: ${WORKSPACE_ROOT}\workspace_manifest.yaml
manifest_version: 1.3.0
manifest_last_modified: 2026-06-20 18:27:28 +08:00
source_commit: 3f751e6
report_scope: workspace setup, skill registry, and projection status
report_is_snapshot: true
truth_source:
  - workspace_manifest.yaml
  - shared/
  - current git commit
staleness_policy: Regenerate after manifest, shared policy, projection, Git baseline, or report script changes.
---

Report is a snapshot. Manifest is the source of truth. If this report conflicts with the manifest, trust the manifest and regenerate the report.

# Workspace Setup Report

Generated: 2026-06-25 22:07:45 +08:00

## Workspace

- Workspace name: `agent-ecosystem-workspace`
- Workspace version: `1.3.0`
- Source of truth: manifest field `workspace.source_of_truth`
- Policy: platform skill directories are projection surfaces only.

## Skills

| Skill | Package | Role | Authority | Execution | Source | Exposures | LegacyPlatform | LegacyProjection | Protocols |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| disk-scan-reporter |  | governance | environment_audit | text_only | skills/disk-scan-reporter | codex:codex.disk-scan-reporter -> ${DATA_ROOT}/codex\skills\disk-scan-reporter | codex | ${DATA_ROOT}/codex\skills\disk-scan-reporter |  |
| windows-ai-storage-governor |  | governance | environment_audit | text_only | skills/windows-ai-storage-governor | codex:codex.windows-ai-storage-governor -> ${DATA_ROOT}/codex\skills\windows-ai-storage-governor<br>claude:claude.windows-ai-storage-governor -> ${WORKSPACE_ROOT}\.claude\skills\windows-ai-storage-governor | codex | ${DATA_ROOT}/codex\skills\windows-ai-storage-governor |  |
| character-generator | character-system | production | generator_write | text_only | packages/character-system/engineering/generation/character-generator | codex:codex.character-generator -> ${DATA_ROOT}/codex\skills\character-generator<br>claude:claude.character-generator -> ${WORKSPACE_ROOT}\.claude\skills\character-generator | codex | ${DATA_ROOT}/codex\skills\character-generator | character_skill_spec, runtime_loop_policy, versioning_policy, workspace_policy, reporting_policy, future_drift_policy |
| character-maintainer | character-system | maintenance | source_patch | text_only | packages/character-system/engineering/maintenance/character-maintainer | codex:codex.character-maintainer -> ${DATA_ROOT}/codex\skills\character-maintainer<br>claude:claude.character-maintainer -> ${WORKSPACE_ROOT}\.claude\skills\character-maintainer | codex | ${DATA_ROOT}/codex\skills\character-maintainer | character_skill_spec, drift_taxonomy, patch_protocol, handoff_format, runtime_loop_policy, versioning_policy, workspace_policy, reporting_policy, future_drift_policy |
| style-doctor | character-system | feedback_diagnosis | diagnosis_text_only | text_only | packages/character-system/engineering/diagnosis/style-doctor | opencode:opencode.style-doctor -> ${USER_HOME}/.config/opencode/skills\style-doctor<br>codex:codex.style-doctor -> ${DATA_ROOT}/codex\skills\style-doctor<br>claude:claude.style-doctor -> ${WORKSPACE_ROOT}\.claude\skills\style-doctor<br>hermes:hermes.style-doctor -> ${DATA_ROOT}/hermes\skills\style-doctor | opencode | ${USER_HOME}/.config/opencode/skills\style-doctor | drift_taxonomy, patch_protocol, handoff_format, runtime_loop_policy, workspace_policy, reporting_policy, future_drift_policy |
| zyc | character-system | runtime_character | runtime_output_only | text_only | packages/character-system/runtime/characters/zyc | opencode:opencode.zyc -> ${USER_HOME}/.config/opencode/skills\zyc<br>codex:codex.zyc -> ${DATA_ROOT}/codex\skills\zyc<br>claude:claude.zyc -> ${WORKSPACE_ROOT}\.claude\skills\zyc<br>hermes:hermes.zyc -> ${DATA_ROOT}/hermes\skills\zyc | opencode | ${USER_HOME}/.config/opencode/skills\zyc | character_skill_spec, drift_taxonomy, patch_protocol, runtime_loop_policy, versioning_policy, workspace_policy, reporting_policy, future_drift_policy |

## Link Status

| Link | Status | Type | Path | Target |
| --- | --- | --- | --- | --- |
| codex disk-scan-reporter | OK | Junction | ${DATA_ROOT}/codex\skills\disk-scan-reporter | ${WORKSPACE_ROOT}\skills\disk-scan-reporter |
| codex windows-ai-storage-governor | OK | Junction | ${DATA_ROOT}/codex\skills\windows-ai-storage-governor | ${WORKSPACE_ROOT}\skills\windows-ai-storage-governor |
| claude windows-ai-storage-governor | OK | Junction | ${WORKSPACE_ROOT}\.claude\skills\windows-ai-storage-governor | ${WORKSPACE_ROOT}\skills\windows-ai-storage-governor |
| codex character-generator | OK | Junction | ${DATA_ROOT}/codex\skills\character-generator | ${WORKSPACE_ROOT}\packages\character-system\engineering\generation\character-generator |
| claude character-generator | OK | Junction | ${WORKSPACE_ROOT}\.claude\skills\character-generator | ${WORKSPACE_ROOT}\packages\character-system\engineering\generation\character-generator |
| codex character-maintainer | OK | Junction | ${DATA_ROOT}/codex\skills\character-maintainer | ${WORKSPACE_ROOT}\packages\character-system\engineering\maintenance\character-maintainer |
| claude character-maintainer | OK | Junction | ${WORKSPACE_ROOT}\.claude\skills\character-maintainer | ${WORKSPACE_ROOT}\packages\character-system\engineering\maintenance\character-maintainer |
| opencode style-doctor | OK | Junction | ${USER_HOME}/.config/opencode/skills\style-doctor | ${WORKSPACE_ROOT}\packages\character-system\engineering\diagnosis\style-doctor |
| codex style-doctor | OK | Junction | ${DATA_ROOT}/codex\skills\style-doctor | ${WORKSPACE_ROOT}\packages\character-system\engineering\diagnosis\style-doctor |
| claude style-doctor | OK | Junction | ${WORKSPACE_ROOT}\.claude\skills\style-doctor | ${WORKSPACE_ROOT}\packages\character-system\engineering\diagnosis\style-doctor |
| hermes style-doctor | OK | Junction | ${DATA_ROOT}/hermes\skills\style-doctor | ${WORKSPACE_ROOT}\packages\character-system\engineering\diagnosis\style-doctor |
| opencode zyc | OK | Junction | ${USER_HOME}/.config/opencode/skills\zyc | ${WORKSPACE_ROOT}\packages\character-system\runtime\characters\zyc |
| codex zyc | OK | Junction | ${DATA_ROOT}/codex\skills\zyc | ${WORKSPACE_ROOT}\packages\character-system\runtime\characters\zyc |
| claude zyc | OK | Junction | ${WORKSPACE_ROOT}\.claude\skills\zyc | ${WORKSPACE_ROOT}\packages\character-system\runtime\characters\zyc |
| hermes zyc | OK | Junction | ${DATA_ROOT}/hermes\skills\zyc | ${WORKSPACE_ROOT}\packages\character-system\runtime\characters\zyc |

## Next Steps

- Run `scripts/check_links.ps1` after any platform or workspace path change.
- Keep source edits inside manifest-declared skill source paths.
- Update `workspace_manifest.yaml` before changing projections or shared protocol locations.
