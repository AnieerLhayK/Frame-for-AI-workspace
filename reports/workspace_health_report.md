---
report_name: workspace_health_report
generated_at: 2026-07-01 20:54:24 +08:00
generated_by: scripts/sync_report.ps1
source_root: ${WORKSPACE_ROOT}
manifest_path: ${WORKSPACE_ROOT}\workspace_manifest.yaml
manifest_version: 1.3.0
manifest_last_modified: 2026-06-20 18:27:28 +08:00
source_commit: 28909d8
report_scope: manifest status, link status, missing files, hardcoded paths, protocol consistency, drift, shared uniqueness, and Git boundaries
report_is_snapshot: true
truth_source:
  - workspace_manifest.yaml
  - shared/
  - current git commit
staleness_policy: Regenerate after manifest, shared policy, projection, Git baseline, or report script changes.
---

Report is a snapshot. Manifest is the source of truth. If this report conflicts with the manifest, trust the manifest and regenerate the report.

# Workspace Health Report

Generated: 2026-07-01 20:54:24 +08:00

## Manifest Status

| Exists | Path | WorkspaceName | Version | SourceOfTruth |
| --- | --- | --- | --- | --- |
| True | ${WORKSPACE_ROOT}\workspace_manifest.yaml | agent-ecosystem-workspace | 1.3.0 | ${WORKSPACE_ROOT} |

## Link Status

| Name | Status | LinkType | TargetExists | LinkPath | ExpectedTarget | ActualTarget |
| --- | --- | --- | --- | --- | --- | --- |
| codex disk-scan-reporter | OK | Junction | True | ${DATA_ROOT}/codex\skills\disk-scan-reporter | ${WORKSPACE_ROOT}\skills\disk-scan-reporter | ${WORKSPACE_ROOT}\skills\disk-scan-reporter |
| codex windows-ai-storage-governor | OK | Junction | True | ${DATA_ROOT}/codex\skills\windows-ai-storage-governor | ${WORKSPACE_ROOT}\skills\windows-ai-storage-governor | ${WORKSPACE_ROOT}\skills\windows-ai-storage-governor |
| claude windows-ai-storage-governor | OK | Junction | True | ${WORKSPACE_ROOT}\.claude\skills\windows-ai-storage-governor | ${WORKSPACE_ROOT}\skills\windows-ai-storage-governor | ${WORKSPACE_ROOT}\skills\windows-ai-storage-governor |
| codex character-generator | OK | Junction | True | ${DATA_ROOT}/codex\skills\character-generator | ${WORKSPACE_ROOT}\packages\character-system\engineering\generation\character-generator | ${WORKSPACE_ROOT}\packages\character-system\engineering\generation\character-generator |
| claude character-generator | OK | Junction | True | ${WORKSPACE_ROOT}\.claude\skills\character-generator | ${WORKSPACE_ROOT}\packages\character-system\engineering\generation\character-generator | ${WORKSPACE_ROOT}\packages\character-system\engineering\generation\character-generator |
| codex character-maintainer | OK | Junction | True | ${DATA_ROOT}/codex\skills\character-maintainer | ${WORKSPACE_ROOT}\packages\character-system\engineering\maintenance\character-maintainer | ${WORKSPACE_ROOT}\packages\character-system\engineering\maintenance\character-maintainer |
| claude character-maintainer | OK | Junction | True | ${WORKSPACE_ROOT}\.claude\skills\character-maintainer | ${WORKSPACE_ROOT}\packages\character-system\engineering\maintenance\character-maintainer | ${WORKSPACE_ROOT}\packages\character-system\engineering\maintenance\character-maintainer |
| opencode style-doctor | OK | Junction | True | ${USER_HOME}/.config/opencode/skills\style-doctor | ${WORKSPACE_ROOT}\packages\character-system\engineering\diagnosis\style-doctor | ${WORKSPACE_ROOT}\packages\character-system\engineering\diagnosis\style-doctor |
| codex style-doctor | OK | Junction | True | ${DATA_ROOT}/codex\skills\style-doctor | ${WORKSPACE_ROOT}\packages\character-system\engineering\diagnosis\style-doctor | ${WORKSPACE_ROOT}\packages\character-system\engineering\diagnosis\style-doctor |
| claude style-doctor | OK | Junction | True | ${WORKSPACE_ROOT}\.claude\skills\style-doctor | ${WORKSPACE_ROOT}\packages\character-system\engineering\diagnosis\style-doctor | ${WORKSPACE_ROOT}\packages\character-system\engineering\diagnosis\style-doctor |
| hermes style-doctor | OK | Junction | True | ${DATA_ROOT}/hermes\skills\style-doctor | ${WORKSPACE_ROOT}\packages\character-system\engineering\diagnosis\style-doctor | ${WORKSPACE_ROOT}\packages\character-system\engineering\diagnosis\style-doctor |
| opencode zyc | OK | Junction | True | ${USER_HOME}/.config/opencode/skills\zyc | ${WORKSPACE_ROOT}\packages\character-system\runtime\characters\zyc | ${WORKSPACE_ROOT}\packages\character-system\runtime\characters\zyc |
| codex zyc | OK | Junction | True | ${DATA_ROOT}/codex\skills\zyc | ${WORKSPACE_ROOT}\packages\character-system\runtime\characters\zyc | ${WORKSPACE_ROOT}\packages\character-system\runtime\characters\zyc |
| claude zyc | OK | Junction | True | ${WORKSPACE_ROOT}\.claude\skills\zyc | ${WORKSPACE_ROOT}\packages\character-system\runtime\characters\zyc | ${WORKSPACE_ROOT}\packages\character-system\runtime\characters\zyc |
| hermes zyc | OK | Junction | True | ${DATA_ROOT}/hermes\skills\zyc | ${WORKSPACE_ROOT}\packages\character-system\runtime\characters\zyc | ${WORKSPACE_ROOT}\packages\character-system\runtime\characters\zyc |

## Missing Required Files

- None.

## Missing Optional Files

| Skill | Kind | RelativePath | Expected | Exists |
| --- | --- | --- | --- | --- |
| character-generator | optional | reports | ${WORKSPACE_ROOT}\packages\character-system\engineering\generation\character-generator\reports | False |
| character-maintainer | optional | reports | ${WORKSPACE_ROOT}\packages\character-system\engineering\maintenance\character-maintainer\reports | False |
| style-doctor | optional | reports | ${WORKSPACE_ROOT}\packages\character-system\engineering\diagnosis\style-doctor\reports | False |

## Hardcoded Paths Remaining

| File | Token | Category |
| --- | --- | --- |
| PROJECT_CONTEXT\session_migrations.json | ${WORKSPACE_ROOT} | other |
| PROJECT_CONTEXT\task_ledger.md | ${WORKSPACE_ROOT} | other |
| USAGE_GUIDES\QUICK_START\claude_code.md | ${WORKSPACE_ROOT} | other |
| WORKSPACE_ENGINEERING\PUBLISH.md | ${WORKSPACE_ROOT} | other |
| WORKSPACE_ENGINEERING\plans\public-repo-plan.md | ${USER_HOME}/.config/opencode/skills | other |
| WORKSPACE_ENGINEERING\plans\public-repo-plan.md | ${WORKSPACE_ROOT} | other |
| WORKSPACE_ENGINEERING\reports\skill_engineering_setup_report.md | ${WORKSPACE_ROOT} | other |
| mcp\README.md | ${WORKSPACE_ROOT} | other |
| mcp\configs\installed-local.mcp.json | ${WORKSPACE_ROOT} | other |
| mcp\configs\wps-agent.mcp.json | ${WORKSPACE_ROOT} | other |
| packages\character-system\reports\runtime-loop\handoffs\HANDOFF-20260604-002.md | ${USER_HOME}/.config/opencode/skills | skill-doc-or-source |
| packages\character-system\reports\runtime-loop\runtime_loop_setup_report.md | ${WORKSPACE_ROOT} | skill-doc-or-source |
| packages\character-system\reports\runtime-loop\validations\VAL-20260623-002-002235-zyc-first-person-authority.md | ${WORKSPACE_ROOT} | skill-doc-or-source |
| packages\character-system\runtime\characters\zyc\reports\discussion_evidence_integrity_patch_20260622.md | ${WORKSPACE_ROOT} | skill-doc-or-source |
| packages\character-system\runtime\characters\zyc\reports\positive_exemplar_feedback_proposal_20260619.md | ${WORKSPACE_ROOT} | skill-doc-or-source |
| packages\character-system\runtime\characters\zyc\reports\runtime_boundary_patch_validation_20260623.md | ${WORKSPACE_ROOT} | skill-doc-or-source |
| reasonix.toml | ${WORKSPACE_ROOT} | other |
| reports\git_governance_report.md | ${WORKSPACE_ROOT} | generated-report |
| reports\hermes\hermes_readiness_report.md | ${WORKSPACE_ROOT} | generated-report |
| reports\hermes\messaging_diagnosis.md | ${WORKSPACE_ROOT} | generated-report |
| reports\hermes\workspace_integration_plan.md | ${DATA_ROOT}/hermes\skills | generated-report |
| reports\hermes\workspace_integration_plan.md | ${WORKSPACE_ROOT} | generated-report |
| reports\manifest_portability_report.md | ${WORKSPACE_ROOT} | generated-report |
| reports\manifest_validation_report.md | ${USER_HOME}/.config/opencode/skills | generated-report |
| reports\manifest_validation_report.md | ${DATA_ROOT}/codex\skills | generated-report |
| reports\manifest_validation_report.md | ${DATA_ROOT}/hermes\skills | generated-report |
| reports\manifest_validation_report.md | ${WORKSPACE_ROOT} | generated-report |
| reports\manifest_validation_report.md | ${WORKSPACE_ROOT}\.claude\skills | generated-report |
| reports\migration_dry_run_report.md | ${DATA_ROOT}/codex\skills | generated-report |
| reports\migration_dry_run_report.md | ${WORKSPACE_ROOT} | generated-report |
| reports\protocol_validation_report.md | ${WORKSPACE_ROOT} | generated-report |
| reports\report_drift_governance_report.md | ${WORKSPACE_ROOT} | generated-report |
| reports\workspace_health_report.md | ${USER_HOME}/.config/opencode/skills | generated-report |
| reports\workspace_health_report.md | ${USER_HOME}/.config/opencode/skills | generated-report |
| reports\workspace_health_report.md | ${DATA_ROOT}/codex\\skills | generated-report |
| reports\workspace_health_report.md | ${DATA_ROOT}/hermes\\skills | generated-report |
| reports\workspace_health_report.md | ${WORKSPACE_ROOT} | generated-report |
| reports\workspace_health_report.md | ${WORKSPACE_ROOT}\\.claude\\skills | generated-report |
| reports\workspace_health_report.md | ${DATA_ROOT}/codex\skills | generated-report |
| reports\workspace_health_report.md | ${DATA_ROOT}/hermes\skills | generated-report |
| reports\workspace_health_report.md | ${WORKSPACE_ROOT} | generated-report |
| reports\workspace_health_report.md | ${WORKSPACE_ROOT}\.claude\skills | generated-report |
| reports\workspace_setup_report.md | ${USER_HOME}/.config/opencode/skills | generated-report |
| reports\workspace_setup_report.md | ${DATA_ROOT}/codex\skills | generated-report |
| reports\workspace_setup_report.md | ${DATA_ROOT}/hermes\skills | generated-report |
| reports\workspace_setup_report.md | ${WORKSPACE_ROOT} | generated-report |
| reports\workspace_setup_report.md | ${WORKSPACE_ROOT}\.claude\skills | generated-report |
| scripts\publish_public.py | ${USER_HOME}/.config/opencode/skills | script |
| scripts\publish_public.py | ${WORKSPACE_ROOT} | script |
| scripts\tests\test_agent_governance.py | ${WORKSPACE_ROOT} | script |
| scripts\tests\test_hermes_workspace_guard.py | ${DATA_ROOT}/hermes\skills | script |
| scripts\tests\test_hermes_workspace_guard.py | ${WORKSPACE_ROOT} | script |
| skills\disk-scan-reporter\reports\disk_report_2026-06-19_002611.md | ${WORKSPACE_ROOT} | skill-doc-or-source |
| skills\disk-scan-reporter\reports\disk_report_2026-06-19_002927.md | ${WORKSPACE_ROOT} | skill-doc-or-source |
| workspace_manifest.yaml | ${USER_HOME}/.config/opencode/skills | manifest-source-of-truth |
| workspace_manifest.yaml | ${DATA_ROOT}/codex\\skills | manifest-source-of-truth |
| workspace_manifest.yaml | ${DATA_ROOT}/hermes\\skills | manifest-source-of-truth |
| workspace_manifest.yaml | ${WORKSPACE_ROOT} | manifest-source-of-truth |
| workspace_manifest.yaml | ${WORKSPACE_ROOT}\\.claude\\skills | manifest-source-of-truth |

Unsafe hardcoded path references outside manifest/generated reports: `24`.

## Protocol Consistency

| Protocol | Required | Path | Exists |
| --- | --- | --- | --- |
| workspace_policy | True | ${WORKSPACE_ROOT}\shared\workspace_policy.md | True |
| discovery_rules | True | ${WORKSPACE_ROOT}\shared\discovery_rules.md | True |
| failure_policy | True | ${WORKSPACE_ROOT}\shared\failure_policy.md | True |
| workspace_path_policy | True | ${WORKSPACE_ROOT}\shared\workspace_path_policy.md | True |
| reporting_policy | True | ${WORKSPACE_ROOT}\shared\reporting_policy.md | True |
| manifest_portability_policy | True | ${WORKSPACE_ROOT}\shared\manifest_portability_policy.md | True |
| session_continuity_policy | True | ${WORKSPACE_ROOT}\shared\session_continuity_policy.md | True |
| agent_governance_policy | True | ${WORKSPACE_ROOT}\shared\agent_governance_policy.md | True |
| delivery_output_policy | True | ${WORKSPACE_ROOT}\shared\delivery_output_policy.md | True |

## Runtime Loop Status

| Component | RelativePath | Path | Exists |
| --- | --- | --- | --- |
| runtime-loop-directory | packages/character-system/reports/runtime-loop | ${WORKSPACE_ROOT}\packages\character-system\reports\runtime-loop | True |
| runtime-loop-policy | packages/character-system/shared/runtime_loop_policy.md | ${WORKSPACE_ROOT}\packages\character-system\shared\runtime_loop_policy.md | True |
| diagnosis-ledger | packages/character-system/reports/runtime-loop/ledgers/diagnosis_ledger.md | ${WORKSPACE_ROOT}\packages\character-system\reports\runtime-loop\ledgers\diagnosis_ledger.md | True |
| patch-ledger | packages/character-system/reports/runtime-loop/ledgers/patch_ledger.md | ${WORKSPACE_ROOT}\packages\character-system\reports\runtime-loop\ledgers\patch_ledger.md | True |
| generalization-ledger | packages/character-system/reports/runtime-loop/ledgers/generalization_ledger.md | ${WORKSPACE_ROOT}\packages\character-system\reports\runtime-loop\ledgers\generalization_ledger.md | True |
| diagnosis-template | packages/character-system/shared/templates/diagnosis_packet.template.md | ${WORKSPACE_ROOT}\packages\character-system\shared\templates\diagnosis_packet.template.md | True |
| handoff-template | packages/character-system/shared/templates/handoff_packet.template.md | ${WORKSPACE_ROOT}\packages\character-system\shared\templates\handoff_packet.template.md | True |
| patch-template | packages/character-system/shared/templates/patch_note.template.md | ${WORKSPACE_ROOT}\packages\character-system\shared\templates\patch_note.template.md | True |
| validation-template | packages/character-system/shared/templates/validation_note.template.md | ${WORKSPACE_ROOT}\packages\character-system\shared\templates\validation_note.template.md | True |
| generalization-template | packages/character-system/shared/templates/generalization_note.template.md | ${WORKSPACE_ROOT}\packages\character-system\shared\templates\generalization_note.template.md | True |

## Protocol Validation Status

| Component | RelativePath | Path | Exists |
| --- | --- | --- | --- |
| protocol-manifest | packages/character-system/shared/protocol_manifest.json | ${WORKSPACE_ROOT}\packages\character-system\shared\protocol_manifest.json | True |
| protocol-validator | scripts/validate_protocols.py | ${WORKSPACE_ROOT}\scripts\validate_protocols.py | True |
| protocol-validation-report | reports/protocol_validation_report.md | ${WORKSPACE_ROOT}\reports\protocol_validation_report.md | True |

## Manifest Portability Status

| Component | RelativePath | Path | Exists |
| --- | --- | --- | --- |
| manifest-portability-policy | shared/manifest_portability_policy.md | ${WORKSPACE_ROOT}\shared\manifest_portability_policy.md | True |
| bootstrap-workspace | scripts/bootstrap_workspace.py | ${WORKSPACE_ROOT}\scripts\bootstrap_workspace.py | True |
| manifest-validator | scripts/validate_manifest.py | ${WORKSPACE_ROOT}\scripts\validate_manifest.py | True |
| migration-dry-run | scripts/migration_dry_run.py | ${WORKSPACE_ROOT}\scripts\migration_dry_run.py | True |
| manifest-validation-report | reports/manifest_validation_report.md | ${WORKSPACE_ROOT}\reports\manifest_validation_report.md | True |
| migration-dry-run-report | reports/migration_dry_run_report.md | ${WORKSPACE_ROOT}\reports\migration_dry_run_report.md | True |
| manifest-portability-report | reports/manifest_portability_report.md | ${WORKSPACE_ROOT}\reports\manifest_portability_report.md | True |

## Projection Drift

- None.

## Shared Uniqueness

- Expected shared source: `shared` resolved from manifest.
- Status: `OK`

## Git Boundaries

| Path | HasGit | BoundaryRole |
| --- | --- | --- |
| ${USER_HOME}/.config/opencode/skills | False | platform-projection |
| ${DATA_ROOT}/codex\skills | False | platform-projection |
| ${DATA_ROOT}/hermes\skills | False | platform-projection |
| ${WORKSPACE_ROOT} | True | source-of-truth |
| ${WORKSPACE_ROOT}\.claude\skills | False | platform-projection |

## Overall Status

- Status: `NEEDS_ATTENTION`
- Required missing count: `0`
- Runtime loop missing count: `0`
- Protocol validation missing count: `0`
- Manifest portability missing count: `0`
- Optional missing count: `3`
- Projection drift count: `0`
- Unsafe hardcoded path count: `24`
