# Reporting Policy

Workspace reports are generated snapshots. They help humans inspect current state, but they are not source-of-truth documents.

## Report Position

Reports may summarize:

- manifest state
- link state
- health status
- Git governance
- drift governance
- protocol validation status
- manifest portability status
- missing required or optional files
- hardcoded path findings

Reports must not define canonical workspace structure. If a report conflicts with the manifest, trust the manifest and regenerate the report.

`reports/agent-requests/` is a narrow exception to the generated-snapshot
model. It stores reviewable governance requests from agents that lack a needed
write capability. A request is not authorization and does not become a truth
source.

`reports/agent-experiments/` is another narrow exception. It accepts only
bounded low-risk records from a validated testing registration, inside that
agent's exact subdirectory. Experiment records are evidence, not activation or
authority.

`reports/agent-requests/` and `reports/agent-experiments/` are controlled
recording surfaces, not generated snapshot collections. They may remain empty
when no request or experiment is active. `agent-experiments` is opt-in and
should not be populated merely to make the directory appear non-empty.

Historical context reports belong under `PROJECT_CONTEXT/reports/history/` and
are not included in current report freshness checks. The historical Hermes
diagnostics were moved there; `reports/hermes/` is retired and is no longer an
authorized write surface.

`PROJECT_CONTEXT/` is a human and agent memory layer, not a generated report layer. Its summaries may point to reports, but they do not replace snapshot headers or report regeneration rules.

## Truth Sources

The truth sources are:

- `workspace_manifest.yaml`
- `shared/`
- current Git commit

Reports can quote resolved absolute paths, but those paths are observations, not authority.

## Staleness

A report is stale when any of these change after report generation:

- `workspace_manifest.yaml`
- any shared policy or protocol used by the report
- current Git commit
- platform projection targets
- required skill source paths
- report generation script

Stale reports should be regenerated before being used for decisions.

Use `python scripts/workspace_cli.py reports status` for a read-only freshness check.
The status command compares snapshot headers, relevant source modification times,
and the Git ordering of the latest relevant source and report commits. A header's
`source_commit` is the generation baseline; it is not required to equal `HEAD`
because source changes and their refreshed report are commonly committed together.
The command must not regenerate or edit reports. Use `--strict` when automation
should return exit code `2` for stale or missing snapshots.

Refresh is always explicit:

```powershell
python scripts/workspace_cli.py reports refresh manifest-validation
python scripts/workspace_cli.py reports refresh protocol-validation
python scripts/workspace_cli.py reports refresh workspace
```

## Standard Header

Every important workspace report should begin with:

```yaml
---
report_name:
generated_at:
generated_by:
source_root:
manifest_path:
manifest_version:
manifest_last_modified:
source_commit:
report_scope:
report_is_snapshot: true
truth_source:
  - workspace_manifest.yaml
  - shared/
  - current git commit
staleness_policy:
---
```

Then include this statement near the top:

```text
Report is a snapshot. Manifest is the source of truth. If this report conflicts with the manifest, trust the manifest and regenerate the report.
```

## Regeneration Rules

Regenerate workspace setup and health reports after:

- manifest changes
- shared policy/protocol changes
- projection changes
- Git baseline changes
- report script changes

Regenerate Git governance reports only after Git boundary work.

Regenerate drift governance reports after report policy, drift policy, or cooperation boundary changes.

Run `scripts/validate_protocols.py` after shared protocol, protocol manifest, runtime-loop template, ledger, or core skill `SHARED_PROTOCOLS.md` changes. It writes `reports/protocol_validation_report.md`, which is a snapshot report and not a truth source.

Run `scripts/validate_manifest.py` and `scripts/migration_dry_run.py` before path migrations. Their reports are snapshots and may contain old absolute paths until regenerated.

## Historical vs Overwritten Reports

Overwrite current-state reports:

- `workspace_setup_report.md`
- `workspace_health_report.md`

Keep historical governance reports unless superseded intentionally:

- `git_governance_report.md`
- `report_drift_governance_report.md`
- `protocol_validation_report.md`
- `manifest_validation_report.md`
- `migration_dry_run_report.md`
- `manifest_portability_report.md`

These retained reports must declare `lifecycle: historical` and
`status: retired` in their front matter when they no longer represent current
state.

Generated per-character reports may be retained or ignored according to each character's Git/privacy policy.
