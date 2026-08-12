# Protocol Index

This file indexes workspace-global protocols. Domain-specific protocols belong
to their package-local shared directory.

## Core Shared Protocols

- `shared/operations/reporting_policy.md`: report snapshot rules and regeneration guidance.
- `shared/workspace/workspace_path_policy.md`: path resolution, source/projection separation, and bounded discovery principles.
- `shared/workspace/discovery_rules.md`: bounded discovery rules and forbidden discovery behaviors.
- `shared/workspace/failure_policy.md`: required vs optional resource failure handling.
- `shared/workspace/workspace_policy.md`: compact source, projection, authority, and
  record contract; detailed procedures stay in their named policy.
- `shared/workspace/manifest_portability_policy.md`: portability, bootstrap discovery, and migration dry-run policy.
- `shared/operations/session_continuity_policy.md`: conversation inventory, backup, path mapping, and recovery rules for source migrations.
- `shared/governance/agent_governance_policy.md`: agent identity, workspace surface
  classification, change-request, worktree, and temporary-lease rules.
- `shared/governance/agent_governance.yaml`: machine-readable agent roles, capabilities,
  surface classes, registration constraints, and lease constraints.
- `shared/governance/agent_registry.yaml`: concrete agent identities, aliases, lifecycle,
  exact scopes, platform references, and external storage/session boundaries.
- `shared/schemas/agent_registration.schema.json`: registration contract shape.
- `shared/operations/delivery_output_policy.md`: separates external deliverables from
  repository artifacts and transient staging files.
- `shared/governance/git_integration_policy.md`: conservative merge preflight, stop
  conditions, post-merge validation, and rollback guidance.
- `shared/governance/agent_governance.yaml`: also registers managed public publishers;
  `scripts/publishing/sync_public_projections.py` synchronizes every registered projection
  after a source update reaches `main`.

## Package Protocols

- `shared/packages/character-system/`: ownership index for the package-local
  shared protocol source.
- `packages/character-system/shared/`: character generation, runtime,
  diagnosis, maintenance, and runtime-loop protocols.

## Optional Policy Libraries

- `shared/claude/policies/`: Claude Code policies that projects import
  explicitly; these are not always-loaded workspace rules.

## Validation

Run:

```powershell
python -m scripts.validation.validate_protocols
```

Current validation output is stored in `reports/current/protocol_validation_report.md`.
