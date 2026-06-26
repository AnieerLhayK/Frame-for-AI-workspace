# Future Drift Policy

This policy defines how to prevent future drift across shared protocols, generated reports, platform projections, and character skills.

## Common Drift Surfaces

Drift is most likely in:

- `style-doctor` diagnosis vocabulary
- `packages/character-system/shared/drift_taxonomy.md`
- ZYC-specific manual evolution
- generator templates and generated character layouts
- workspace reports
- platform projection paths
- scripts that resolve manifest or shared paths
- shared protocol registry and schema files

## Detecting Drift

Use these checks:

- Run `scripts/check_links.ps1` after projection or source path changes.
- Run `scripts/validate_protocols.py` after shared protocol, runtime-loop template, ledger, or core skill `SHARED_PROTOCOLS.md` changes.
- Regenerate reports after manifest or shared policy changes.
- Compare `style-doctor` drift terms against `packages/character-system/shared/drift_taxonomy.md`.
- Ask `character-maintainer` to classify character changes as generalizable or character-specific.
- Check whether reports are older than the manifest, relevant shared docs, or current Git commit.

## Preventing Drift

- Keep `workspace_manifest.yaml` as the source for roots, projections, and registry data.
- Keep `packages/character-system/shared/protocol_manifest.json` as the registry for shared protocol contract checks.
- Keep shared vocabulary in shared docs before copying terms into skill-specific docs.
- Do not edit source through platform projection surfaces.
- Do not promote one mature character's special structure into generator defaults without review.
- Treat reports as snapshots and regenerate them instead of manually correcting old report facts.

## A. Style-Doctor Taxonomy Drift

`style-doctor` drift vocabulary must stay aligned with `packages/character-system/shared/drift_taxonomy.md`.

If a new drift type is needed:

1. Update `packages/character-system/shared/drift_taxonomy.md`.
2. Review `style-doctor` prompts, checklists, and docs.
3. Update only the minimal affected style-doctor files.
4. Record whether the change affects `character-maintainer` patch handoff.

Do not invent runtime-only taxonomy terms that bypass shared vocabulary.

## B. ZYC Evolution Drift

`zyc` may continue to evolve manually. Mature characters can contain handcrafted choices, exceptions, and runtime lessons.

Do not automatically generalize ZYC-specific structure into `character-generator`.

When ZYC evolves, `character-maintainer` should classify the lesson as:

- `generalizable`: candidate for generator docs/templates after separate review
- `character-specific`: keep only in ZYC
- `uncertain`: record in a report, do not promote yet

## C. Reports Drift

Reports are snapshots. Manifest, shared docs, and Git commit state are authoritative.

When manifest, shared policy, link state, or Git baseline changes, regenerate related reports rather than editing the observed values manually.

## D. Platform/Source Confusion

The source-of-truth is `workspace_manifest.yaml -> workspace.source_of_truth`.

Platform directories declared by `workspace_manifest.yaml -> platform_roots` and `projections[]` are projection surfaces. Do not maintain source files directly through them.

If a projection and source disagree, trust source and run link checks.

Do not infer role or authority from a platform exposure. Runtime and engineering
source placement describe lifecycle role; the manifest contract remains
authoritative.

## E. Manifest/Link Drift

Projection state must be validated through `scripts/check_links.ps1`.

`setup_links.ps1`, `check_links.ps1`, and `sync_report.ps1` should continue to read from `workspace_manifest.yaml`. Do not reintroduce duplicated link arrays.

## Ownership

- `style-doctor`: runtime diagnosis and patch suggestions on any compatible exposure.
- `character-maintainer`: character repair, drift patching, and generalizable-vs-specific classification when the agent can verify source, Git, and validation.
- `character-generator`: generation workflow and templates when the agent has the required Python and write capabilities, not mature-character maintenance.
- `zyc`: character-specific runtime artifact and manually evolved style source with runtime-output-only authority.
- shared policies: vocabulary, path, reporting, and governance source.
- `scripts/validate_protocols.py`: shared protocol contract drift check and protocol validation report generator.
