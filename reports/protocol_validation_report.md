---
report_name: protocol_validation_report
generated_at: 2026-06-28 23:11:51 +0800
generated_by: scripts/validate_protocols.py
source_root: ${WORKSPACE_ROOT}
manifest_path: ${WORKSPACE_ROOT}\workspace_manifest.yaml
protocol_manifest_path: ${WORKSPACE_ROOT}\packages\character-system\shared\protocol_manifest.json
source_commit: ac1ca2b
report_scope: character-system protocol contract validation
report_is_snapshot: true
truth_source:
  - workspace_manifest.yaml
  - packages/character-system/shared/protocol_manifest.json
  - shared/
  - current git commit
---

Report is a snapshot. Manifest and shared protocol sources are the source of truth. If this report conflicts with source files, trust the source files and rerun validation.

# Protocol Validation Report

## 1. Summary

- Errors: `0`
- Warnings: `1`
- Info: `36`
- Package and workspace protocol dependencies checked: `13`
- Core skills checked: `4`
- Runtime loop templates checked: `5`
- Runtime loop ledgers checked: `3`

## 2. Errors

- None.

## 3. Warnings

- WARNING: schemas are present as lightweight field contracts; deep instance validation is not yet enforced

## 4. Checked Protocol Dependencies

| id | path | required | exists |
| --- | --- | --- | --- |
| character_skill_spec | packages/character-system/shared/character_skill_spec.md | True | True |
| drift_taxonomy | packages/character-system/shared/drift_taxonomy.md | True | True |
| handoff_format | packages/character-system/shared/handoff_format.md | True | True |
| patch_protocol | packages/character-system/shared/patch_protocol.md | True | True |
| versioning_policy | packages/character-system/shared/versioning_policy.md | True | True |
| workspace_policy | shared/workspace_policy.md | True | True |
| discovery_rules | shared/discovery_rules.md | True | True |
| failure_policy | shared/failure_policy.md | True | True |
| workspace_path_policy | shared/workspace_path_policy.md | True | True |
| reporting_policy | shared/reporting_policy.md | True | True |
| future_drift_policy | packages/character-system/shared/future_drift_policy.md | True | True |
| runtime_loop_policy | packages/character-system/shared/runtime_loop_policy.md | True | True |
| manifest_portability_policy | shared/manifest_portability_policy.md | True | True |

## 5. Checked Core Skills

| id | path | exists | shared_protocols_exists | required_refs | missing_refs | unclear_refs |
| --- | --- | --- | --- | --- | --- | --- |
| character-generator | packages/character-system/engineering/generation/character-generator | True | True | 6 | [] | [] |
| character-maintainer | packages/character-system/engineering/maintenance/character-maintainer | True | True | 9 | [] | [] |
| style-doctor | packages/character-system/engineering/diagnosis/style-doctor | True | True | 7 | [] | [] |
| zyc | packages/character-system/runtime/characters/zyc | True | True | 8 | [] | [] |

## 6. Checked Runtime Loop Templates

| id | path | required | exists |
| --- | --- | --- | --- |
| diagnosis_packet | packages/character-system/shared/templates/diagnosis_packet.template.md | True | True |
| handoff_packet | packages/character-system/shared/templates/handoff_packet.template.md | True | True |
| patch_note | packages/character-system/shared/templates/patch_note.template.md | True | True |
| validation_note | packages/character-system/shared/templates/validation_note.template.md | True | True |
| generalization_note | packages/character-system/shared/templates/generalization_note.template.md | True | True |

## 7. Checked Ledgers

| id | path | required | exists |
| --- | --- | --- | --- |
| diagnosis_ledger | packages/character-system/reports/runtime-loop/ledgers/diagnosis_ledger.md | True | True |
| patch_ledger | packages/character-system/reports/runtime-loop/ledgers/patch_ledger.md | True | True |
| generalization_ledger | packages/character-system/reports/runtime-loop/ledgers/generalization_ledger.md | True | True |

## 8. Schema Status

| path | exists | valid_json |
| --- | --- | --- |
| packages/character-system/shared/schemas/protocol_manifest.schema.json | True | True |
| packages/character-system/shared/schemas/diagnosis_packet.schema.json | True | True |
| packages/character-system/shared/schemas/handoff_packet.schema.json | True | True |
| packages/character-system/shared/schemas/patch_note.schema.json | True | True |
| packages/character-system/shared/schemas/validation_note.schema.json | True | True |
| packages/character-system/shared/schemas/generalization_note.schema.json | True | True |

## 9. Next Recommendations

- Run `python scripts/validate_protocols.py` after changing `shared/`, runtime-loop templates, ledgers, or core skill `SHARED_PROTOCOLS.md` files.
- Keep schema enforcement lightweight until runtime-loop packet instances need automated validation.
- Treat warnings as review prompts; only errors should block protocol contract changes.
