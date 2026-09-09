# Glossary

## source-of-truth

The authoritative source for a given decision. For paths and workspace registry data, this is `workspace_manifest.yaml`.

## projection surface

A platform-facing runtime entry point declared under `workspace_manifest.yaml -> platform_roots` and `projections[]`. It should point back to source and not become an independent source root.

## role

The ecosystem responsibility of a skill, such as production, maintenance, feedback diagnosis, or runtime character behavior.

## authority

The durable effects a skill may produce. Authority is fixed by the skill contract and is not granted by platform exposure.

## execution mode

The task-level operating level, such as `text_only`, `record_write`, or `source_patch`. It activates only a permitted subset of the skill's authority.

## exposure

A manifest declaration connecting one source skill to a platform projection. Exposure controls discovery and invocation, not ownership or write permission.

## protocol layers

Root `shared/` contains workspace-global governance. Package-local `shared/`
contains domain protocols used only by skills that declare that package.

## runtime loop

The durable operating loop for runtime drift: diagnosis, handoff, maintainer decision, patch note, validation note, optional generalization note, and ledger update.

## diagnosis packet

A runtime failure record produced by `style-doctor` before maintenance work begins.

## handoff packet

A record that transfers a diagnosis from `style-doctor` to `character-maintainer` for review.

## patch ledger

The runtime loop index of patch decisions and validation/generalization status.

## generalization backlog

The place for lessons that might affect generator or shared protocol design after maintainer review.

## manifest

`workspace_manifest.yaml`, the machine-readable registry for workspace roots, skills, projections, protocols, discovery, failure handling, and portability metadata.

## validator

A script that checks workspace contracts. Current validators include `scripts/validation/validate_protocols.py` and `scripts/validation/validate_manifest.py`.

## report snapshot

A report generated at a point in time. It may contain absolute paths and old commit IDs. It does not override manifest-routed protocols or current Git state.

## drift

A mismatch between intended behavior and actual behavior. In this workspace it often means style, protocol, report, projection, or path drift.

## ZYC evolution

Manual and runtime-driven evolution of the ZYC-inspired character skill. It is character-specific by default.

## generator generalization

The process of promoting a validated lesson from character maintenance into generator or shared protocol design. It requires explicit review and should not happen from one patch alone.

## planning record

A `PLAN-…` record that describes prospective work, its dependencies, acceptance criteria, claim, and execution links. It coordinates work but grants no write authority.

## decision map

A `MAP-…` record for a multi-session destination, its associated planning records, settled decisions, unresolved matters, and explicit scope boundaries.

## execution record

A `TASK-…` outcome record created when work actually begins. It is the only planning-domain record that can carry active write authorization.

## claim

A time-bounded coordination reservation on a ready planning record. Claims expire after 24 hours and prevent duplicate work; they do not grant authority.

## remote-only repository

An external GitHub repository intentionally retained without a local checkout.
It is recorded in `PROJECT_CONTEXT/references/remote_only_repositories.yaml`,
not in workspace skill registration or a local launcher map.

## pending retirement

A remote-only registry state for a local checkout proposed for retirement but
not yet proven removed. It grants no deletion authority.

## local launcher registry

A machine-local map such as `${DATA_ROOT}/claude\project_roots.json` that may
refer only to existing local roots. A retirement removes only entries that
exactly match the retired checkout path.

## development branch

The shared line of unfinished and completed development, used concurrently by all agents. This workspace uses `dev`.

## stable integration branch

The line containing complete batches that passed validation and code-review. This workspace uses `main`.

## concurrent development session

A session with its own active TASK that may edit the shared development branch alongside other sessions, including the same files. Sessions coordinate overlapping edits and serialize Git mutations.
