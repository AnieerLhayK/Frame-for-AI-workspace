# Context Structure Refactoring

Use this method when a workspace memory or tooling directory has accumulated
scattered registries, reports, adapters, and historical records.

## Design the seam first

Keep a small, stable interface at the root and hide implementation detail in
responsibility domains. Prefer one deep loader or CLI interface over many
callers that know file layout. The canonical source owns behavior; generated
projections and old entry points are adapters, never independent sources.

## Migration rules

1. Inventory consumers before moving a path: scripts, tests, manifests,
   publishers, active documentation, and human workflows.
2. Separate live source, generated snapshots, and historical evidence.
3. Move append-only facts only after their writers and readers share the new
   path; do not maintain two writable copies.
4. Preserve old machine-readable shapes through generated compatibility
   projections when direct consumers exist.
5. Record old-to-new aliases and leave historical records unchanged.
6. Validate canonical sources, projection parity, references, and public
   publishing boundaries before committing.

## AI navigation

Provide one lightweight machine index with read conditions and path aliases.
Keep the root README as human navigation, and expose live summaries through
the existing workspace CLI. History should be addressable but excluded from
ordinary startup context.

## Reusable verification

Run focused loader and adapter tests first, then structural validators, full
script tests, report freshness checks, health, and `git diff --check`. Compare
the resolved change scope with the task record before finalization. This same
sequence applies to scripts responsibility refactors and PROJECT_CONTEXT
directory migrations.
