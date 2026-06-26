---
report_name: migration_dry_run_report
generated_at: 2026-06-09 20:13:09 +0800
generated_by: scripts/migration_dry_run.py
source_root: ${WORKSPACE_ROOT}
manifest_path: ${WORKSPACE_ROOT}\workspace_manifest.yaml
source_commit: 35a70d6
report_scope: migration dry-run simulation
report_is_snapshot: true
truth_source:
  - workspace_manifest.yaml
  - shared/
  - current git commit
---

Report is a snapshot. No files, directories, or links were moved.

# Migration Dry Run Report

## Scenario

- Scenario: `codex-root-change`

## Affected Manifest Fields

| field | current | simulated |
| --- | --- | --- |
| platform_roots.codex | ${DATA_ROOT}/codex\skills | ${DATA_ROOT}/codex\skills-migration-test |
| projections[0].link_path | ${DATA_ROOT}/codex\skills\character-generator | ${DATA_ROOT}/codex\skills-migration-test\character-generator |
| projections[1].link_path | ${DATA_ROOT}/codex\skills\character-maintainer | ${DATA_ROOT}/codex\skills-migration-test\character-maintainer |
| projections[4].link_path | ${DATA_ROOT}/codex\skills\zyc | ${DATA_ROOT}/codex\skills-migration-test\zyc |
| shared.projection_paths.codex | None | ${DATA_ROOT}/codex\skills-migration-test\shared |
| skills[0].projection_path | ${DATA_ROOT}/codex\skills\character-generator | ${DATA_ROOT}/codex\skills-migration-test\character-generator |
| skills[1].projection_path | ${DATA_ROOT}/codex\skills\character-maintainer | ${DATA_ROOT}/codex\skills-migration-test\character-maintainer |

## Affected Projections

| field | current | simulated |
| --- | --- | --- |
| platform_roots.codex | ${DATA_ROOT}/codex\skills | ${DATA_ROOT}/codex\skills-migration-test |
| projections[0].link_path | ${DATA_ROOT}/codex\skills\character-generator | ${DATA_ROOT}/codex\skills-migration-test\character-generator |
| projections[1].link_path | ${DATA_ROOT}/codex\skills\character-maintainer | ${DATA_ROOT}/codex\skills-migration-test\character-maintainer |
| projections[4].link_path | ${DATA_ROOT}/codex\skills\zyc | ${DATA_ROOT}/codex\skills-migration-test\zyc |
| shared.projection_paths.codex | None | ${DATA_ROOT}/codex\skills-migration-test\shared |
| skills[0].projection_path | ${DATA_ROOT}/codex\skills\character-generator | ${DATA_ROOT}/codex\skills-migration-test\character-generator |
| skills[1].projection_path | ${DATA_ROOT}/codex\skills\character-maintainer | ${DATA_ROOT}/codex\skills-migration-test\character-maintainer |

## Affected Scripts

- scripts/bootstrap_workspace.py
- scripts/validate_manifest.py
- scripts/migration_dry_run.py
- scripts/setup_links.ps1
- scripts/check_links.ps1
- scripts/sync_report.ps1

## Affected Reports

- reports/workspace_setup_report.md
- reports/workspace_health_report.md
- reports/manifest_validation_report.md
- reports/migration_dry_run_report.md
- reports/manifest_portability_report.md

## Affected Skill Docs

- core skill SHARED_PROTOCOLS.md files only if shared policy paths change
- skill source files are not moved by this dry run

## Required Manual Steps

- Review the simulated manifest changes.
- Move workspace or platform directories manually outside this dry run if desired.
- Update `workspace_manifest.yaml` intentionally after the real move.
- Run bootstrap, manifest validation, protocol validation, sync report, and link check.
- Recreate platform junctions only after explicit approval.

## Safe To Automate?

- Manifest analysis: yes.
- File moves: no.
- Junction relinking: no.

## Risks

- Absolute platform roots are local deployment data and may not exist on the target machine.
- Reports may contain stale absolute paths until regenerated.
- Existing platform tools may cache old projection paths.

## Rollback Advice

- Keep the current Git commit as the source checkpoint.
- Do not delete old platform projections until new link checks pass.
- Revert manifest path edits if validation or link checks fail.

## Notes

- Codex platform projection root changes; source paths remain workspace-relative.
