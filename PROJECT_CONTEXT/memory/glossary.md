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

A script that checks workspace contracts. Current validators include `scripts/validate_protocols.py` and `scripts/validate_manifest.py`.

## report snapshot

A report generated at a point in time. It may contain absolute paths and old commit IDs. It does not override manifest-routed protocols or current Git state.

## drift

A mismatch between intended behavior and actual behavior. In this workspace it often means style, protocol, report, projection, or path drift.

## ZYC evolution

Manual and runtime-driven evolution of the ZYC-inspired character skill. It is character-specific by default.

## generator generalization

The process of promoting a validated lesson from character maintenance into generator or shared protocol design. It requires explicit review and should not happen from one patch alone.
