# Protocol Index

This file indexes workspace-global protocols. Domain-specific protocols belong
to their package-local shared directory.

## Core Shared Protocols

- `shared/reporting_policy.md`: report snapshot rules and regeneration guidance.
- `shared/workspace_path_policy.md`: path resolution, source/projection separation, and bounded discovery principles.
- `shared/discovery_rules.md`: bounded discovery rules and forbidden discovery behaviors.
- `shared/failure_policy.md`: required vs optional resource failure handling.
- `shared/workspace_policy.md`: workspace source center, platform roots, and report positioning.
- `shared/manifest_portability_policy.md`: portability, bootstrap discovery, and migration dry-run policy.
- `shared/session_continuity_policy.md`: conversation inventory, backup, path mapping, and recovery rules for source migrations.
- `shared/agent_governance_policy.md`: agent identity, workspace surface
  classification, change-request, worktree, and temporary-lease rules.
- `shared/agent_governance.yaml`: machine-readable agent roles, capabilities,
  surface classes, registration constraints, and lease constraints.
- `shared/agent_registry.yaml`: concrete agent identities, aliases, lifecycle,
  exact scopes, platform references, and external storage/session boundaries.
- `shared/schemas/agent_registration.schema.json`: registration contract shape.
- `shared/delivery_output_policy.md`: separates external deliverables from
  repository artifacts and transient staging files.
- `shared/git_integration_policy.md`: conservative merge preflight, stop
  conditions, post-merge validation, and rollback guidance.
- `shared/agent_governance.yaml`: also registers managed public publishers;
  `scripts/sync_public_projections.py` synchronizes every registered projection
  after a source update reaches `main`.

## Package Protocols

- `packages/character-system/shared/`: character generation, runtime,
  diagnosis, maintenance, and runtime-loop protocols.

## Optional Policy Libraries

- `shared/claude/policies/`: Claude Code policies that projects import
  explicitly; these are not always-loaded workspace rules.

## Validation

Run:

```powershell
python scripts\validate_protocols.py
```

Current validation output is stored in `reports/protocol_validation_report.md`.
