# Workspace Policy

The manifest-declared workspace root is the source center for the agent skill system.

Compatibility entry points may exist, but they must resolve to the manifest-declared source of truth.

Workspace root discovery should use bounded bootstrap lookup for `workspace_manifest.yaml`. See `shared/discovery_rules.md` and `shared/manifest_portability_policy.md`.

## Source Center

The source center is declared by:

```text
workspace_manifest.yaml -> workspace.source_of_truth
```

All concrete source changes should happen there.

Related skills may be grouped under `packages[]`; unrelated skills may live
under `skills/`. Package and skill source paths remain workspace-relative and
must not encode platform ownership.

## Platform Directories

Platform directories are declared by:

```text
workspace_manifest.yaml -> platform_roots
```

They should contain projections to workspace source, not independent source copies.

Platform roots can be local absolute paths because they are deployment entry points for installed tools. They are not portable source layout.

## Role, Authority, Execution, And Exposure

Skill governance uses four separate dimensions:

- `role`: what the skill is responsible for.
- `authority`: what durable state or output class the skill may produce.
- `execution_modes`: how the current agent may exercise that authority in the current environment.
- `exposures`: which platform loading surfaces currently discover the skill.

Platform exposure grants discoverability only. It does not grant write access, expand authority, or prove that the platform has the tools needed to execute the skill safely.

The manifest records current exposures through `skills[].exposures[].projection_id`, which resolves to `projections[]`. During the compatibility phase, `skills[].platform` and `skills[].projection_path` remain as aliases for the first exposure. New logic should prefer `exposures[]`.

## Do Not Edit Link Surfaces

Do not directly edit skill files through platform directories. Even if a linked file opens correctly, navigate back to the manifest-declared `skills[].source_path` before making source changes.

## Execution Capability Modes

Skills may declare one or more lightweight execution modes:

- `text_only`: read available context and return text. Do not write files or update ledgers.
- `record_write`: write only task-owned diagnosis, handoff, report, validation, or ledger records allowed by the skill's role. Do not modify skill source, shared protocols, manifests, or generator assets.
- `source_patch`: modify manifest-resolved workspace source within the skill's existing authority boundary.
- `environment_write`: modify user-approved external environment paths or tool
  configuration within a governance skill's explicit plan and rollback boundary.

Use the skill's declared default mode first. Enter `record_write` or `source_patch` only when the user requested work that requires it and the agent can resolve the workspace source, inspect relevant existing changes, and verify the result. If any required capability cannot be confirmed, downgrade to `text_only` and provide the proposed record or patch as text.

Enter `environment_write` only when the user approved an exact plan or action
set, the skill declares environment-mutation authority, and each action has a
verified rollback path. Environment write approval does not imply cleanup or
deletion approval.

An execution mode grants no additional role authority. For example, `record_write` does not let `style-doctor` write patch records, and `source_patch` does not let `character-maintainer` edit generator templates. Do not self-upgrade based only on model confidence.

## Agent Governance

Skill authority and agent authority are separate checks. A skill may allow
`record_write`, but the invoking agent must also be permitted to write the
target workspace surface.

Codex and Claude Code are the default structural maintainers. Hermes and
OpenCode are default record producers with bounded paths. Unregistered agents
may read, invoke explicitly supplied skills, and submit change requests, but
they may not register skills or modify structural files.

The classification table, temporary lease lifecycle, and machine-readable
matrix are defined by:

```text
shared/agent_governance_policy.md
shared/agent_governance.yaml
```

Use `workspace agent check` before an agent writes outside its normal role.
Denied structural work should become a change request, not an improvised
registration edit.

## Link Ownership

Links are created and checked by:

```text
scripts/setup_links.ps1
scripts/check_links.ps1
```

Both scripts read `workspace_manifest.yaml`; do not duplicate projection definitions inside scripts.

## Reports

Workspace reports are generated under:

```text
reports/
```

Do not place reports at the D drive root.

Reports are snapshots, not source-of-truth documents. The source of truth
remains `workspace_manifest.yaml`, workspace-global and package-local protocol
sources, and the current Git commit. If a report conflicts with those sources,
trust the sources and regenerate the report. See `shared/reporting_policy.md`.

## External Deliverables

Files intended for use outside this repository belong under:

```text
workspace_manifest.yaml -> output_roots.workspace
```

This external delivery root does not replace repository-native source,
tracked reports, runtime records, fixtures, or tests. Transient working files
still belong in tool staging. Classification and directory layout are defined
by `shared/delivery_output_policy.md`.

## Project Context

`PROJECT_CONTEXT/` is the long-term memory layer for humans and agents. It is the recommended entry point for new sessions, but it is not a source-of-truth layer. If it conflicts with `workspace_manifest.yaml`, `shared/`, current Git state, or a freshly generated report, update `PROJECT_CONTEXT/` after verifying the source layer.
