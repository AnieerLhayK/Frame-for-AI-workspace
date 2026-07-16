---
report_name: manifest_validation_report
generated_at: 2026-07-15 21:01:19 +0800
generated_by: scripts/validate_manifest.py
source_root: ${WORKSPACE_ROOT}
manifest_path: ${WORKSPACE_ROOT}\workspace_manifest.yaml
source_commit: 408a267
report_scope: manifest portability and consistency validation
report_is_snapshot: true
truth_source:
  - workspace_manifest.yaml
  - shared/
  - current git commit
---

Report is a snapshot. Manifest is the source of truth. If this report conflicts with the manifest, trust the manifest and rerun validation.

# Manifest Validation Report

## Summary

- Errors: `0`
- Warnings: `2`
- Info: `171`

## Errors

- None.

## Warnings

- WARNING: absolute path field may need portability review: external_roots.research
- WARNING: absolute path field may need portability review: external_roots.raw_skills

## Path Checks

| field | declared | resolved | required | exists |
| --- | --- | --- | --- | --- |
| shared.source_path | shared | ${WORKSPACE_ROOT}\shared | True | True |
| packages[character-system].source_path | packages/character-system | ${WORKSPACE_ROOT}\packages\character-system | True | True |
| packages[character-system].runtime_path | packages/character-system/runtime | ${WORKSPACE_ROOT}\packages\character-system\runtime | True | True |
| packages[character-system].engineering_path | packages/character-system/engineering | ${WORKSPACE_ROOT}\packages\character-system\engineering | True | True |
| packages[character-system].shared_path | packages/character-system/shared | ${WORKSPACE_ROOT}\packages\character-system\shared | True | True |
| packages[character-system].reports_path | packages/character-system/reports | ${WORKSPACE_ROOT}\packages\character-system\reports | True | True |
| packages[character-system].protocol_manifest | packages/character-system/shared/protocol_manifest.json | ${WORKSPACE_ROOT}\packages\character-system\shared\protocol_manifest.json | True | True |
| skills[disk-scan-reporter].source_path | skills/disk-scan-reporter | ${WORKSPACE_ROOT}\skills\disk-scan-reporter | True | True |
| skills[disk-scan-reporter].required_files:SKILL.md | SKILL.md | ${WORKSPACE_ROOT}\skills\disk-scan-reporter\SKILL.md | True | True |
| skills[disk-scan-reporter].required_files:README.md | README.md | ${WORKSPACE_ROOT}\skills\disk-scan-reporter\README.md | True | True |
| skills[disk-scan-reporter].required_files:agents/openai.yaml | agents/openai.yaml | ${WORKSPACE_ROOT}\skills\disk-scan-reporter\agents\openai.yaml | True | True |
| skills[disk-scan-reporter].required_files:config/audit_policy.json | config/audit_policy.json | ${WORKSPACE_ROOT}\skills\disk-scan-reporter\config\audit_policy.json | True | True |
| skills[disk-scan-reporter].required_files:config/scan_config.json | config/scan_config.json | ${WORKSPACE_ROOT}\skills\disk-scan-reporter\config\scan_config.json | True | True |
| skills[disk-scan-reporter].required_files:references/coverage_schema.md | references/coverage_schema.md | ${WORKSPACE_ROOT}\skills\disk-scan-reporter\references\coverage_schema.md | True | True |
| skills[disk-scan-reporter].required_files:references/report_schema.json | references/report_schema.json | ${WORKSPACE_ROOT}\skills\disk-scan-reporter\references\report_schema.json | True | True |
| skills[disk-scan-reporter].required_files:scripts/audit_guard.py | scripts/audit_guard.py | ${WORKSPACE_ROOT}\skills\disk-scan-reporter\scripts\audit_guard.py | True | True |
| skills[disk-scan-reporter].required_files:scripts/disk_scan.py | scripts/disk_scan.py | ${WORKSPACE_ROOT}\skills\disk-scan-reporter\scripts\disk_scan.py | True | True |
| skills[disk-scan-reporter].required_files:tests/test_audit_guard.py | tests/test_audit_guard.py | ${WORKSPACE_ROOT}\skills\disk-scan-reporter\tests\test_audit_guard.py | True | True |
| skills[disk-scan-reporter].required_files:tests/test_disk_scan.py | tests/test_disk_scan.py | ${WORKSPACE_ROOT}\skills\disk-scan-reporter\tests\test_disk_scan.py | True | True |
| skills[windows-ai-storage-governor].source_path | skills/windows-ai-storage-governor | ${WORKSPACE_ROOT}\skills\windows-ai-storage-governor | True | True |
| skills[windows-ai-storage-governor].required_files:SKILL.md | SKILL.md | ${WORKSPACE_ROOT}\skills\windows-ai-storage-governor\SKILL.md | True | True |
| skills[windows-ai-storage-governor].required_files:agents/openai.yaml | agents/openai.yaml | ${WORKSPACE_ROOT}\skills\windows-ai-storage-governor\agents\openai.yaml | True | True |
| skills[windows-ai-storage-governor].required_files:references/safety-policy.md | references/safety-policy.md | ${WORKSPACE_ROOT}\skills\windows-ai-storage-governor\references\safety-policy.md | True | True |
| skills[windows-ai-storage-governor].required_files:references/path-classification.md | references/path-classification.md | ${WORKSPACE_ROOT}\skills\windows-ai-storage-governor\references\path-classification.md | True | True |
| skills[windows-ai-storage-governor].required_files:references/migration-runbook.md | references/migration-runbook.md | ${WORKSPACE_ROOT}\skills\windows-ai-storage-governor\references\migration-runbook.md | True | True |
| skills[windows-ai-storage-governor].required_files:references/report-schema.md | references/report-schema.md | ${WORKSPACE_ROOT}\skills\windows-ai-storage-governor\references\report-schema.md | True | True |
| skills[windows-ai-storage-governor].required_files:references/tool-adapters.md | references/tool-adapters.md | ${WORKSPACE_ROOT}\skills\windows-ai-storage-governor\references\tool-adapters.md | True | True |
| skills[windows-ai-storage-governor].required_files:scripts/audit-environment.ps1 | scripts/audit-environment.ps1 | ${WORKSPACE_ROOT}\skills\windows-ai-storage-governor\scripts\audit-environment.ps1 | True | True |
| skills[windows-ai-storage-governor].required_files:scripts/inspect-path.ps1 | scripts/inspect-path.ps1 | ${WORKSPACE_ROOT}\skills\windows-ai-storage-governor\scripts\inspect-path.ps1 | True | True |
| skills[windows-ai-storage-governor].required_files:scripts/build-migration-plan.ps1 | scripts/build-migration-plan.ps1 | ${WORKSPACE_ROOT}\skills\windows-ai-storage-governor\scripts\build-migration-plan.ps1 | True | True |
| skills[windows-ai-storage-governor].required_files:scripts/validate-migration.ps1 | scripts/validate-migration.ps1 | ${WORKSPACE_ROOT}\skills\windows-ai-storage-governor\scripts\validate-migration.ps1 | True | True |
| skills[windows-ai-storage-governor].required_files:fixtures/safe-sandbox-profile.json | fixtures/safe-sandbox-profile.json | ${WORKSPACE_ROOT}\skills\windows-ai-storage-governor\fixtures\safe-sandbox-profile.json | True | True |
| skills[character-generator].source_path | packages/character-system/engineering/generation/character-generator | ${WORKSPACE_ROOT}\packages\character-system\engineering\generation\character-generator | True | True |
| skills[character-generator].required_files:SKILL.md | SKILL.md | ${WORKSPACE_ROOT}\packages\character-system\engineering\generation\character-generator\SKILL.md | True | True |
| skills[character-generator].required_files:README.md | README.md | ${WORKSPACE_ROOT}\packages\character-system\engineering\generation\character-generator\README.md | True | True |
| skills[character-generator].required_files:SHARED_PROTOCOLS.md | SHARED_PROTOCOLS.md | ${WORKSPACE_ROOT}\packages\character-system\engineering\generation\character-generator\SHARED_PROTOCOLS.md | True | True |
| skills[character-generator].required_files:scripts/build_character.py | scripts/build_character.py | ${WORKSPACE_ROOT}\packages\character-system\engineering\generation\character-generator\scripts\build_character.py | True | True |
| skills[character-generator].required_files:templates/character_SKILL.template.md | templates/character_SKILL.template.md | ${WORKSPACE_ROOT}\packages\character-system\engineering\generation\character-generator\templates\character_SKILL.template.md | True | True |
| skills[character-maintainer].source_path | packages/character-system/engineering/maintenance/character-maintainer | ${WORKSPACE_ROOT}\packages\character-system\engineering\maintenance\character-maintainer | True | True |
| skills[character-maintainer].required_files:SKILL.md | SKILL.md | ${WORKSPACE_ROOT}\packages\character-system\engineering\maintenance\character-maintainer\SKILL.md | True | True |
| skills[character-maintainer].required_files:README.md | README.md | ${WORKSPACE_ROOT}\packages\character-system\engineering\maintenance\character-maintainer\README.md | True | True |
| skills[character-maintainer].required_files:SHARED_PROTOCOLS.md | SHARED_PROTOCOLS.md | ${WORKSPACE_ROOT}\packages\character-system\engineering\maintenance\character-maintainer\SHARED_PROTOCOLS.md | True | True |
| skills[character-maintainer].required_files:prompts/feedback_patch_prompt.md | prompts/feedback_patch_prompt.md | ${WORKSPACE_ROOT}\packages\character-system\engineering\maintenance\character-maintainer\prompts\feedback_patch_prompt.md | True | True |
| skills[character-maintainer].required_files:docs/architecture.md | docs/architecture.md | ${WORKSPACE_ROOT}\packages\character-system\engineering\maintenance\character-maintainer\docs\architecture.md | True | True |
| skills[style-doctor].source_path | packages/character-system/engineering/diagnosis/style-doctor | ${WORKSPACE_ROOT}\packages\character-system\engineering\diagnosis\style-doctor | True | True |
| skills[style-doctor].required_files:SKILL.md | SKILL.md | ${WORKSPACE_ROOT}\packages\character-system\engineering\diagnosis\style-doctor\SKILL.md | True | True |
| skills[style-doctor].required_files:README.md | README.md | ${WORKSPACE_ROOT}\packages\character-system\engineering\diagnosis\style-doctor\README.md | True | True |
| skills[style-doctor].required_files:SHARED_PROTOCOLS.md | SHARED_PROTOCOLS.md | ${WORKSPACE_ROOT}\packages\character-system\engineering\diagnosis\style-doctor\SHARED_PROTOCOLS.md | True | True |
| skills[style-doctor].required_files:prompts/drift_diagnosis_prompt.md | prompts/drift_diagnosis_prompt.md | ${WORKSPACE_ROOT}\packages\character-system\engineering\diagnosis\style-doctor\prompts\drift_diagnosis_prompt.md | True | True |
| skills[style-doctor].required_files:prompts/patch_suggestion_prompt.md | prompts/patch_suggestion_prompt.md | ${WORKSPACE_ROOT}\packages\character-system\engineering\diagnosis\style-doctor\prompts\patch_suggestion_prompt.md | True | True |
| skills[zyc].source_path | packages/character-system/runtime/characters/zyc | ${WORKSPACE_ROOT}\packages\character-system\runtime\characters\zyc | True | True |
| skills[zyc].required_files:SKILL.md | SKILL.md | ${WORKSPACE_ROOT}\packages\character-system\runtime\characters\zyc\SKILL.md | True | True |
| skills[zyc].required_files:README.md | README.md | ${WORKSPACE_ROOT}\packages\character-system\runtime\characters\zyc\README.md | True | True |
| skills[zyc].required_files:SHARED_PROTOCOLS.md | SHARED_PROTOCOLS.md | ${WORKSPACE_ROOT}\packages\character-system\runtime\characters\zyc\SHARED_PROTOCOLS.md | True | True |
| skills[zyc].required_files:references/voice_card.md | references/voice_card.md | ${WORKSPACE_ROOT}\packages\character-system\runtime\characters\zyc\references\voice_card.md | True | True |
| skills[zyc].required_files:references/evaluation_rubric.md | references/evaluation_rubric.md | ${WORKSPACE_ROOT}\packages\character-system\runtime\characters\zyc\references\evaluation_rubric.md | True | True |
| skills[zyc].required_files:prompts/rewrite_prompt.md | prompts/rewrite_prompt.md | ${WORKSPACE_ROOT}\packages\character-system\runtime\characters\zyc\prompts\rewrite_prompt.md | True | True |
| skills[grill-me].source_path | external-skills/productivity/grill-me | ${WORKSPACE_ROOT}\external-skills\productivity\grill-me | True | True |
| skills[grill-me].required_files:SKILL.md | SKILL.md | ${WORKSPACE_ROOT}\external-skills\productivity\grill-me\SKILL.md | True | True |
| skills[grilling].source_path | external-skills/productivity/grilling | ${WORKSPACE_ROOT}\external-skills\productivity\grilling | True | True |
| skills[grilling].required_files:SKILL.md | SKILL.md | ${WORKSPACE_ROOT}\external-skills\productivity\grilling\SKILL.md | True | True |
| skills[handoff].source_path | external-skills/productivity/handoff | ${WORKSPACE_ROOT}\external-skills\productivity\handoff | True | True |
| skills[handoff].required_files:SKILL.md | SKILL.md | ${WORKSPACE_ROOT}\external-skills\productivity\handoff\SKILL.md | True | True |
| skills[diagnosing-bugs].source_path | external-skills/engineering/diagnosing-bugs | ${WORKSPACE_ROOT}\external-skills\engineering\diagnosing-bugs | True | True |
| skills[diagnosing-bugs].required_files:SKILL.md | SKILL.md | ${WORKSPACE_ROOT}\external-skills\engineering\diagnosing-bugs\SKILL.md | True | True |
| skills[tdd].source_path | external-skills/engineering/tdd | ${WORKSPACE_ROOT}\external-skills\engineering\tdd | True | True |
| skills[tdd].required_files:SKILL.md | SKILL.md | ${WORKSPACE_ROOT}\external-skills\engineering\tdd\SKILL.md | True | True |
| skills[tdd].required_files:tests.md | tests.md | ${WORKSPACE_ROOT}\external-skills\engineering\tdd\tests.md | True | True |
| skills[tdd].required_files:mocking.md | mocking.md | ${WORKSPACE_ROOT}\external-skills\engineering\tdd\mocking.md | True | True |
| skills[code-review].source_path | external-skills/engineering/code-review | ${WORKSPACE_ROOT}\external-skills\engineering\code-review | True | True |
| skills[code-review].required_files:SKILL.md | SKILL.md | ${WORKSPACE_ROOT}\external-skills\engineering\code-review\SKILL.md | True | True |
| skills[codebase-design].source_path | external-skills/engineering/codebase-design | ${WORKSPACE_ROOT}\external-skills\engineering\codebase-design | True | True |
| skills[codebase-design].required_files:SKILL.md | SKILL.md | ${WORKSPACE_ROOT}\external-skills\engineering\codebase-design\SKILL.md | True | True |
| skills[writing-great-skills].source_path | external-skills/engineering/writing-great-skills | ${WORKSPACE_ROOT}\external-skills\engineering\writing-great-skills | True | True |
| skills[writing-great-skills].required_files:SKILL.md | SKILL.md | ${WORKSPACE_ROOT}\external-skills\engineering\writing-great-skills\SKILL.md | True | True |
| skills[writing-great-skills].required_files:GLOSSARY.md | GLOSSARY.md | ${WORKSPACE_ROOT}\external-skills\engineering\writing-great-skills\GLOSSARY.md | True | True |
| protocols[workspace_policy].path | shared/workspace_policy.md | ${WORKSPACE_ROOT}\shared\workspace_policy.md | True | True |
| protocols[discovery_rules].path | shared/discovery_rules.md | ${WORKSPACE_ROOT}\shared\discovery_rules.md | True | True |
| protocols[failure_policy].path | shared/failure_policy.md | ${WORKSPACE_ROOT}\shared\failure_policy.md | True | True |
| protocols[workspace_path_policy].path | shared/workspace_path_policy.md | ${WORKSPACE_ROOT}\shared\workspace_path_policy.md | True | True |
| protocols[reporting_policy].path | shared/reporting_policy.md | ${WORKSPACE_ROOT}\shared\reporting_policy.md | True | True |
| protocols[manifest_portability_policy].path | shared/manifest_portability_policy.md | ${WORKSPACE_ROOT}\shared\manifest_portability_policy.md | True | True |
| protocols[session_continuity_policy].path | shared/session_continuity_policy.md | ${WORKSPACE_ROOT}\shared\session_continuity_policy.md | True | True |
| protocols[agent_governance_policy].path | shared/agent_governance_policy.md | ${WORKSPACE_ROOT}\shared\agent_governance_policy.md | True | True |
| protocols[delivery_output_policy].path | shared/delivery_output_policy.md | ${WORKSPACE_ROOT}\shared\delivery_output_policy.md | True | True |

## Projection Checks

| id | link_path | target_path | link_exists | target_exists | target_matches_source |
| --- | --- | --- | --- | --- | --- |
| codex.grill-me | ${DATA_ROOT}/codex\skills\grill-me | ${WORKSPACE_ROOT}\external-skills\productivity\grill-me | True | True | True |
| claude.grill-me | ${WORKSPACE_ROOT}\.claude\skills\grill-me | ${WORKSPACE_ROOT}\external-skills\productivity\grill-me | True | True | True |
| codex.grilling | ${DATA_ROOT}/codex\skills\grilling | ${WORKSPACE_ROOT}\external-skills\productivity\grilling | True | True | True |
| claude.grilling | ${WORKSPACE_ROOT}\.claude\skills\grilling | ${WORKSPACE_ROOT}\external-skills\productivity\grilling | True | True | True |
| codex.handoff | ${DATA_ROOT}/codex\skills\handoff | ${WORKSPACE_ROOT}\external-skills\productivity\handoff | True | True | True |
| claude.handoff | ${WORKSPACE_ROOT}\.claude\skills\handoff | ${WORKSPACE_ROOT}\external-skills\productivity\handoff | True | True | True |
| codex.diagnosing-bugs | ${DATA_ROOT}/codex\skills\diagnosing-bugs | ${WORKSPACE_ROOT}\external-skills\engineering\diagnosing-bugs | True | True | True |
| claude.diagnosing-bugs | ${WORKSPACE_ROOT}\.claude\skills\diagnosing-bugs | ${WORKSPACE_ROOT}\external-skills\engineering\diagnosing-bugs | True | True | True |
| codex.tdd | ${DATA_ROOT}/codex\skills\tdd | ${WORKSPACE_ROOT}\external-skills\engineering\tdd | True | True | True |
| claude.tdd | ${WORKSPACE_ROOT}\.claude\skills\tdd | ${WORKSPACE_ROOT}\external-skills\engineering\tdd | True | True | True |
| codex.code-review | ${DATA_ROOT}/codex\skills\code-review | ${WORKSPACE_ROOT}\external-skills\engineering\code-review | True | True | True |
| claude.code-review | ${WORKSPACE_ROOT}\.claude\skills\code-review | ${WORKSPACE_ROOT}\external-skills\engineering\code-review | True | True | True |
| codex.codebase-design | ${DATA_ROOT}/codex\skills\codebase-design | ${WORKSPACE_ROOT}\external-skills\engineering\codebase-design | True | True | True |
| claude.codebase-design | ${WORKSPACE_ROOT}\.claude\skills\codebase-design | ${WORKSPACE_ROOT}\external-skills\engineering\codebase-design | True | True | True |
| codex.writing-great-skills | ${DATA_ROOT}/codex\skills\writing-great-skills | ${WORKSPACE_ROOT}\external-skills\engineering\writing-great-skills | True | True | True |
| claude.writing-great-skills | ${WORKSPACE_ROOT}\.claude\skills\writing-great-skills | ${WORKSPACE_ROOT}\external-skills\engineering\writing-great-skills | True | True | True |
| codex.disk-scan-reporter | ${DATA_ROOT}/codex\skills\disk-scan-reporter | ${WORKSPACE_ROOT}\skills\disk-scan-reporter | True | True | True |
| codex.windows-ai-storage-governor | ${DATA_ROOT}/codex\skills\windows-ai-storage-governor | ${WORKSPACE_ROOT}\skills\windows-ai-storage-governor | True | True | True |
| claude.windows-ai-storage-governor | ${WORKSPACE_ROOT}\.claude\skills\windows-ai-storage-governor | ${WORKSPACE_ROOT}\skills\windows-ai-storage-governor | True | True | True |
| codex.character-generator | ${DATA_ROOT}/codex\skills\character-generator | ${WORKSPACE_ROOT}\packages\character-system\engineering\generation\character-generator | True | True | True |
| claude.character-generator | ${WORKSPACE_ROOT}\.claude\skills\character-generator | ${WORKSPACE_ROOT}\packages\character-system\engineering\generation\character-generator | True | True | True |
| codex.character-maintainer | ${DATA_ROOT}/codex\skills\character-maintainer | ${WORKSPACE_ROOT}\packages\character-system\engineering\maintenance\character-maintainer | True | True | True |
| claude.character-maintainer | ${WORKSPACE_ROOT}\.claude\skills\character-maintainer | ${WORKSPACE_ROOT}\packages\character-system\engineering\maintenance\character-maintainer | True | True | True |
| opencode.style-doctor | ${USER_HOME}/.config/opencode/skills\style-doctor | ${WORKSPACE_ROOT}\packages\character-system\engineering\diagnosis\style-doctor | True | True | True |
| codex.style-doctor | ${DATA_ROOT}/codex\skills\style-doctor | ${WORKSPACE_ROOT}\packages\character-system\engineering\diagnosis\style-doctor | True | True | True |
| claude.style-doctor | ${WORKSPACE_ROOT}\.claude\skills\style-doctor | ${WORKSPACE_ROOT}\packages\character-system\engineering\diagnosis\style-doctor | True | True | True |
| hermes.style-doctor | ${DATA_ROOT}/hermes\skills\style-doctor | ${WORKSPACE_ROOT}\packages\character-system\engineering\diagnosis\style-doctor | True | True | True |
| opencode.zyc | ${USER_HOME}/.config/opencode/skills\zyc | ${WORKSPACE_ROOT}\packages\character-system\runtime\characters\zyc | True | True | True |
| codex.zyc | ${DATA_ROOT}/codex\skills\zyc | ${WORKSPACE_ROOT}\packages\character-system\runtime\characters\zyc | True | True | True |
| claude.zyc | ${WORKSPACE_ROOT}\.claude\skills\zyc | ${WORKSPACE_ROOT}\packages\character-system\runtime\characters\zyc | True | True | True |
| hermes.zyc | ${DATA_ROOT}/hermes\skills\zyc | ${WORKSPACE_ROOT}\packages\character-system\runtime\characters\zyc | True | True | True |

## Absolute Path Fields

| field | value | allowed |
| --- | --- | --- |
| workspace.source_of_truth | ${WORKSPACE_ROOT} | True |
| platform_roots.codex | ${DATA_ROOT}/codex\skills | True |
| platform_roots.claude | ${WORKSPACE_ROOT}\.claude\skills | True |
| platform_roots.opencode | ${USER_HOME}/.config/opencode/skills | True |
| platform_roots.hermes | ${DATA_ROOT}/hermes\skills | True |
| session_stores.claude.data_root | ${DATA_ROOT}/claude | True |
| session_stores.opencode.data_root | ${DATA_ROOT}/opencode\current-share | True |
| output_roots.workspace | ${DATA_ROOT}/out/workspace | True |
| external_roots.research | ${WORKSPACE_ROOT}\research | False |
| external_roots.raw_skills | ${WORKSPACE_ROOT}\research\skills | False |
| skills[0].projection_path | ${DATA_ROOT}/codex\skills\disk-scan-reporter | True |
| skills[1].projection_path | ${DATA_ROOT}/codex\skills\windows-ai-storage-governor | True |
| skills[2].projection_path | ${DATA_ROOT}/codex\skills\character-generator | True |
| skills[3].projection_path | ${DATA_ROOT}/codex\skills\character-maintainer | True |
| skills[4].projection_path | ${USER_HOME}/.config/opencode/skills\style-doctor | True |
| skills[5].projection_path | ${USER_HOME}/.config/opencode/skills\zyc | True |
| skills[6].projection_path | ${DATA_ROOT}/codex\skills\grill-me | True |
| skills[7].projection_path | ${DATA_ROOT}/codex\skills\grilling | True |
| skills[8].projection_path | ${DATA_ROOT}/codex\skills\handoff | True |
| skills[9].projection_path | ${DATA_ROOT}/codex\skills\diagnosing-bugs | True |
| skills[10].projection_path | ${DATA_ROOT}/codex\skills\tdd | True |
| skills[11].projection_path | ${DATA_ROOT}/codex\skills\code-review | True |
| skills[12].projection_path | ${DATA_ROOT}/codex\skills\codebase-design | True |
| skills[13].projection_path | ${DATA_ROOT}/codex\skills\writing-great-skills | True |
| projections[0].link_path | ${DATA_ROOT}/codex\skills\grill-me | True |
| projections[1].link_path | ${WORKSPACE_ROOT}\.claude\skills\grill-me | True |
| projections[2].link_path | ${DATA_ROOT}/codex\skills\grilling | True |
| projections[3].link_path | ${WORKSPACE_ROOT}\.claude\skills\grilling | True |
| projections[4].link_path | ${DATA_ROOT}/codex\skills\handoff | True |
| projections[5].link_path | ${WORKSPACE_ROOT}\.claude\skills\handoff | True |
| projections[6].link_path | ${DATA_ROOT}/codex\skills\diagnosing-bugs | True |
| projections[7].link_path | ${WORKSPACE_ROOT}\.claude\skills\diagnosing-bugs | True |
| projections[8].link_path | ${DATA_ROOT}/codex\skills\tdd | True |
| projections[9].link_path | ${WORKSPACE_ROOT}\.claude\skills\tdd | True |
| projections[10].link_path | ${DATA_ROOT}/codex\skills\code-review | True |
| projections[11].link_path | ${WORKSPACE_ROOT}\.claude\skills\code-review | True |
| projections[12].link_path | ${DATA_ROOT}/codex\skills\codebase-design | True |
| projections[13].link_path | ${WORKSPACE_ROOT}\.claude\skills\codebase-design | True |
| projections[14].link_path | ${DATA_ROOT}/codex\skills\writing-great-skills | True |
| projections[15].link_path | ${WORKSPACE_ROOT}\.claude\skills\writing-great-skills | True |
| projections[16].link_path | ${DATA_ROOT}/codex\skills\disk-scan-reporter | True |
| projections[17].link_path | ${DATA_ROOT}/codex\skills\windows-ai-storage-governor | True |
| projections[18].link_path | ${WORKSPACE_ROOT}\.claude\skills\windows-ai-storage-governor | True |
| projections[19].link_path | ${DATA_ROOT}/codex\skills\character-generator | True |
| projections[20].link_path | ${WORKSPACE_ROOT}\.claude\skills\character-generator | True |
| projections[21].link_path | ${DATA_ROOT}/codex\skills\character-maintainer | True |
| projections[22].link_path | ${WORKSPACE_ROOT}\.claude\skills\character-maintainer | True |
| projections[23].link_path | ${USER_HOME}/.config/opencode/skills\style-doctor | True |
| projections[24].link_path | ${DATA_ROOT}/codex\skills\style-doctor | True |
| projections[25].link_path | ${WORKSPACE_ROOT}\.claude\skills\style-doctor | True |
| projections[26].link_path | ${DATA_ROOT}/hermes\skills\style-doctor | True |
| projections[27].link_path | ${USER_HOME}/.config/opencode/skills\zyc | True |
| projections[28].link_path | ${DATA_ROOT}/codex\skills\zyc | True |
| projections[29].link_path | ${WORKSPACE_ROOT}\.claude\skills\zyc | True |
| projections[30].link_path | ${DATA_ROOT}/hermes\skills\zyc | True |

## Future Relative Candidates

| field | reason |
| --- | --- |
| skills[disk-scan-reporter].projection_path | can be derived from platform_roots plus skill id when scripts support it |
| skills[windows-ai-storage-governor].projection_path | can be derived from platform_roots plus skill id when scripts support it |
| skills[character-generator].projection_path | can be derived from platform_roots plus skill id when scripts support it |
| skills[character-maintainer].projection_path | can be derived from platform_roots plus skill id when scripts support it |
| skills[style-doctor].projection_path | can be derived from platform_roots plus skill id when scripts support it |
| skills[zyc].projection_path | can be derived from platform_roots plus skill id when scripts support it |
| skills[grill-me].projection_path | can be derived from platform_roots plus skill id when scripts support it |
| skills[grilling].projection_path | can be derived from platform_roots plus skill id when scripts support it |
| skills[handoff].projection_path | can be derived from platform_roots plus skill id when scripts support it |
| skills[diagnosing-bugs].projection_path | can be derived from platform_roots plus skill id when scripts support it |
| skills[tdd].projection_path | can be derived from platform_roots plus skill id when scripts support it |
| skills[code-review].projection_path | can be derived from platform_roots plus skill id when scripts support it |
| skills[codebase-design].projection_path | can be derived from platform_roots plus skill id when scripts support it |
| skills[writing-great-skills].projection_path | can be derived from platform_roots plus skill id when scripts support it |
| projections[codex.grill-me].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[claude.grill-me].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[codex.grilling].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[claude.grilling].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[codex.handoff].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[claude.handoff].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[codex.diagnosing-bugs].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[claude.diagnosing-bugs].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[codex.tdd].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[claude.tdd].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[codex.code-review].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[claude.code-review].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[codex.codebase-design].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[claude.codebase-design].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[codex.writing-great-skills].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[claude.writing-great-skills].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[codex.disk-scan-reporter].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[codex.windows-ai-storage-governor].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[claude.windows-ai-storage-governor].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[codex.character-generator].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[claude.character-generator].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[codex.character-maintainer].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[claude.character-maintainer].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[opencode.style-doctor].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[codex.style-doctor].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[claude.style-doctor].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[hermes.style-doctor].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[opencode.zyc].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[codex.zyc].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[claude.zyc].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
| projections[hermes.zyc].link_path | platform-local deployment path; could be templated from platform_roots in a future manifest version |
