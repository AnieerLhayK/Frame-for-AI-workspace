# Stable Skill Catalog Partitioning

Use categories when one central registry has become a coordination bottleneck,
or when a source tree has several durable ownership domains. Do not add a layer
just because a directory is large: first show that category ownership, review,
or discoverability benefits exceed the cost of new references and tooling.

## Choose And Stabilize Categories

- Classify by the user's primary task, not implementation language, platform,
  team, or temporary project phase.
- Give each skill one primary category. Keep cross-cutting responsibility in
  metadata and references instead of duplicate registrations.
- Prefer a small stable vocabulary. Add a category only when several current or
  planned sources need it and no existing category fits without distortion.
- Keep owner-local records next to their sources; let a root index point to
  owner registries. Runtime consumers should use one loader to aggregate these
  records into a compatibility view.
- Keep package protocols separate from package-owned skill and tool inventory.
  Register only independently invocable tools; do not duplicate helper scripts.

## When To Reclassify

Reclassify only when the skill's primary user task has materially changed, the
existing category no longer gives maintainers a truthful ownership/review
boundary, or a category has become a coherent independent domain. A rename,
script refactor, platform addition, or temporary project does not by itself
justify moving a skill.

## Safe Migration Sequence

1. Record the intended category map and exact old/new paths. Exclude historical
   records and generated snapshots unless the task explicitly owns them.
2. Add a central loader and tests while the old root registry still works; keep
   the aggregated runtime view stable.
3. Generate owner registries from the existing canonical records, preserving
   IDs, authority, execution modes, required files, and exposures exactly.
4. Move sources to approved destinations and update registries, projections,
   import roots, scripts, task routes, docs, tests, and publisher contracts.
5. Scan current source references for old paths and validate every local link
   and required file. Keep historical snapshots unchanged.
6. Compare the loader's effective IDs and contracts with the pre-migration
   snapshot; test platform discovery and public staging before integration.
7. Remove the legacy root records only after all active consumers use the
   loader. Publish only through the registered publisher after integration.

## Make Future Moves Easier

Prefer manifest-relative source paths and skill-relative sibling references.
Derive Workspace roots from the discovered manifest or bounded parent lookup;
avoid fixed-depth `parents[n]` assumptions in source scripts. Give each catalog
an explicit index instead of having consumers scan folders. Let README and
policy explain ownership while IDs remain stable. Add a link/reference test so
future moves fail visibly rather than silently keeping stale paths alive.

This method is locally validated by the 2026 Workspace catalog partitioning;
reapply it only after checking current task routes and platform projection
contracts.
