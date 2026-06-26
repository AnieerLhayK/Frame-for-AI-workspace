# Decisions

## Manifest-Declared Workspace Is The Only Source Center

- decision: Treat `workspace_manifest.yaml -> workspace.source_of_truth` as the only source-of-truth workspace.
- reason: Prevent drift between platform projections and editable source.
- date if known: 2026-05-27 baseline governance.
- consequence: Git operations and source edits belong in the manifest-declared workspace root.

## Platform Directories Are Projection Surfaces

- decision: Platform directories declared by `workspace_manifest.yaml -> platform_roots` and `projections[]` are runtime projection surfaces.
- reason: Codex and OpenCode need platform entry points, but those paths should not become independent source roots.
- date if known: 2026-05-27 Git governance.
- consequence: Do not commit or maintain source from platform directories.

## Exposure Does Not Define Role Or Authority

- decision: Separate each skill's role, durable authority, execution mode, and platform exposure.
- reason: A skill may be useful on multiple platforms without changing what it is allowed to do.
- date if known: 2026-06-09 architecture compatibility phase.
- consequence: Agents and scripts must not infer ownership or write permission from the invoking platform or exposure path.

## Legacy Platform Fields Remain Compatibility Aliases

- decision: Keep `skills[].platform` and `skills[].projection_path` temporarily as aliases for the first `exposures[]` entry.
- reason: Existing scripts and external consumers may still depend on the old single-platform shape.
- date if known: 2026-06-09 architecture compatibility phase.
- consequence: New logic uses `exposures[]`; validators ensure legacy aliases stay synchronized until retirement.

## Shared Is Single-Source

- decision: `shared/` is a single protocol source, projected to platforms when needed.
- reason: Copying shared protocols into skills creates protocol drift.
- date if known: manifest established before current governance series.
- consequence: Skills reference shared protocols instead of embedding copies.

## Reports Are Snapshots

- decision: Reports summarize observations and are not source-of-truth documents.
- reason: Reports can become stale after manifest, shared policy, Git, or projection changes.
- date if known: 2026-05-27 report drift governance.
- consequence: If a report conflicts with manifest/shared/current Git, trust the source and regenerate the report.

## Manifest Is Machine-Readable Source Of Truth

- decision: `workspace_manifest.yaml` owns roots, skills, projections, protocols, discovery, failure policy, and portability metadata.
- reason: Centralized registry is safer than scattered path assumptions.
- date if known: manifest exists as workspace source before this context layer.
- consequence: Scripts should read the manifest rather than duplicate path arrays.

## Generator Does Not Maintain Mature Characters

- decision: `character-generator` creates initial scaffolds and generation workflow assets.
- reason: Mature characters accumulate manual evolution that generation templates should not overwrite.
- date if known: reinforced during report drift and runtime loop governance.
- consequence: Existing character repairs go to `character-maintainer`.

## Maintainer Does Not Directly Modify Generator

- decision: `character-maintainer` may record generalization notes but should not directly edit generator templates from one character patch.
- reason: Character-specific fixes can damage future generated characters if promoted too early.
- date if known: runtime loop governance.
- consequence: Generator changes require reviewed generalization evidence.

## Style-Doctor Does Not Apply Patches

- decision: `style-doctor` diagnoses runtime drift and creates diagnosis/handoff records.
- reason: Diagnosis and maintenance are separate responsibilities.
- date if known: runtime loop governance.
- consequence: Patches are accepted/rejected/deferred by `character-maintainer`.

## ZYC Experience Is Not Automatically Generalized

- decision: ZYC-specific runtime lessons default to character-specific.
- reason: ZYC is a mature manually evolved character with special style constraints.
- date if known: runtime loop governance.
- consequence: Generator promotion requires a maintainer-approved generalization note.

## Git Tracks Workspace, Not Platform Roots

- decision: Git baseline belongs to the manifest-declared workspace root; platform `.git` metadata is not primary.
- reason: Avoid competing histories and source confusion.
- date if known: 2026-05-27 Git governance.
- consequence: Projection `.git.disabled-*` metadata remains for future archive/review.

## Full-Drive Discovery Is Forbidden

- decision: Bootstrap discovery is bounded upward from a known start path.
- reason: Full-drive scans are slow, unsafe, and can bind the project to unrelated folders.
- date if known: manifest portability/bootstrap discovery phase.
- consequence: Use `scripts/bootstrap_workspace.py` and manifest discovery policy.

## Agent Review Must Stay Independent

- decision: User judgment decides subjective style fit, but agent review must independently flag engineering and safety risk.
- reason: A character output can feel appealing while still drifting facts, overfitting motifs, weakening privacy boundaries, or generalizing a character-specific trick too early.
- date if known: 2026-06-04 ZYC validation case review.
- consequence: Validation notes should separate user aesthetic judgment from agent checks and record disagreement when needed.
