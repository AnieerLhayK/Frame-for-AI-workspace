# Workspace Policy

This policy is the compact workspace-wide contract. Task-specific procedures
belong to their named policy or task route; machine-enforced facts belong in
the manifest and governance YAML.

## Source and layout

`workspace_manifest.yaml -> workspace.source_of_truth` is the source center.
Make source changes there, never through a platform projection. Workspace-native
standalone skills belong in `skills/`; related skills may use a package-local
shared layer under `packages/`. Source paths are workspace-relative and do not
encode platform ownership.

Raw external skill repositories are research inputs outside this Git source.
`external-skills/` is only the tracked, reviewed adaptation layer declared by
`external_roots.adapted_skills`. Record a new raw skill in
`PROJECT_CONTEXT/todo/external-skills.md`; before exposure, record provenance,
license, applicability, adaptation, validation, manifest registration, and
exposure. Do not place raw clones in either source layer. Discovery alone
grants no runtime exposure.

## Paths and projections

Resolve source, package, protocol, and projection paths through the manifest.
Platform roots and links are local deployment data; they may be absolute, but
their targets must remain workspace-relative. One source may have many
projections. Do not copy source to achieve multi-platform exposure or edit a
linked platform path as source.

New readers resolve `skills[].exposures[]` through `projections[]`.
`skills[].platform` and `skills[].projection_path` remain compatibility aliases
for the first exposure until consumers migrate.

Use bounded discovery and visible failure handling from
`shared/workspace/discovery_rules.md` and `shared/workspace/failure_policy.md`. Required resources
stop the workflow; optional resources warn and use degraded mode. Do not guess
paths, silently borrow another package's protocol, or scan drives.

## Role, authority, execution, exposure

These dimensions are independent:

- `role`: responsibility;
- `authority`: durable effect class;
- `execution_modes`: how that authority may be exercised now;
- `exposures`: platform discovery surfaces.

Exposure grants discoverability only. Skill execution modes are `text_only`,
`record_write`, `source_patch`, and `environment_write`. Start with the
declared default. Enter a write mode only when the user requested it, source
and validation are resolved, and the acting agent is authorized. An execution
mode never expands the skill's role or an agent's path scope.

Plugin-provided skills are registered under `workspace_manifest.yaml ->
plugin_skills` without copied source or local projections. Registration may
identify a skill by short or qualified id, but never bypasses task records,
agent checks, or path scope.

`environment_write` additionally requires an exact user-approved action plan,
explicit environment-mutation authority, and a verified rollback path. It does
not authorize cleanup or deletion.

Agent identity, task records, capabilities, leases, surface classification, and
write checks are defined by `shared/governance/agent_governance.yaml` and
`shared/governance/agent_governance_policy.md`. A denied structural action becomes a
change request, not an improvised registration or projection edit.

## Records, reports, and delivery

Every workspace or workspace-mediated external mutation requires an active task
record before the first write. The record ID is distinct from the task route;
pass it to write checks and the active workflow check. Read-only work is exempt.

Reports are snapshots, not truth sources. If a report conflicts with the
manifest, shared/package protocol, or current Git state, trust the source and
regenerate it. Reporting lifecycle rules live in `shared/operations/reporting_policy.md`.
External deliverables resolve through `output_roots.workspace`; their
classification and layout live in `shared/operations/delivery_output_policy.md`.

## Integration and publication

Links are created and checked only by the manifest-driven link scripts. Git
integration follows `shared/governance/git_integration_policy.md`. Registered public
projections are synchronized only after the source change reaches `main`, with
an active `external_write` record, by the aggregate publisher whose targets are
declared in `shared/governance/agent_governance.yaml`. Direct edits to public checkouts are
forbidden.

## Memory

`PROJECT_CONTEXT/` is durable memory and routing, not a stronger truth source
than the manifest, shared protocols, Git state, or a freshly generated report.
