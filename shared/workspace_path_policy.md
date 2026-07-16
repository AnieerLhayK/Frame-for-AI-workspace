# Workspace Path Policy

The workspace is manifest-driven. Paths used by skills, scripts, and reports must be resolved through `workspace_manifest.yaml` or expressed relative to the workspace, shared root, or current skill directory.

## Why Absolute Paths Are Avoided

Hardcoded absolute paths make the ecosystem brittle. If a skill moves from one directory to another, references to the old location keep working only by accident, and linked platform projections can silently drift away from the real source.

Use these forms instead:

- `workspace-relative`: `packages/character-system/engineering/generation/character-generator`
- `package-relative`: `packages/character-system/shared/patch_protocol.md`
- `skill-relative`: `scripts/build_character.py`
- `manifest-declared`: `skills[].source_path`, `projections[].link_path`, `protocols[].path`
- `exposure-declared`: `skills[].exposures[].projection_id` resolved through `projections[]`

## Manifest Is Source Of Truth

`workspace_manifest.yaml` owns:

- workspace metadata
- platform roots
- shared root
- skill registry
- projection definitions
- protocol registry
- bounded discovery rules

Scripts should read the manifest instead of duplicating link arrays or protocol lists.

Manifest portability rules are defined in `shared/manifest_portability_policy.md`. The manifest may centralize local absolute platform roots, but workspace-internal source paths should remain workspace-relative wherever practical.

The manifest may also declare local external roots such as
`output_roots.workspace`. Documentation should reference the manifest field
instead of repeating the current machine path.

External skill paths are resolved through `workspace_manifest.yaml`:

- raw research inputs: `external_roots.raw_skills`;
- curated adapted sources: `external_roots.adapted_skills`;
- native standalone sources: `skills/`.

Raw research inputs are outside the workspace source tree and are never a
platform projection target. An adapted external skill must be copied or
transformed into the curated workspace path, then registered in the manifest
before it can be exposed.

## Projection Path Is Not Source Path

Platform projection paths are compatibility surfaces for tools such as Codex and OpenCode. They may be junctions or symlinks.

Do not treat a projection path as the editable source. Source edits belong in `skills[].source_path` resolved against `workspace.source_of_truth`.

One source may have multiple platform projections. Do not duplicate skill source to achieve multi-platform exposure. Resolve each exposure through its referenced projection and verify that every projection target matches the same manifest-declared source path.

## Discovery Must Be Bounded

Discovery is limited to the current skill directory, at most 5 parent directories, the manifest-declared workspace, and manifest-declared platform projections.

Bounded discovery prevents accidental coupling to unrelated folders and avoids slow or dangerous full-drive scans.

Use `scripts/bootstrap_workspace.py` for a bounded bootstrap check before assuming the workspace root.

## Required And Optional Must Be Separate

Required files stop the workflow when missing. Optional files may produce warnings and degraded mode.

This distinction prevents silent corruption while allowing reports, examples, history, or archives to be absent without breaking core skill behavior.

## Report Paths

Reports may contain resolved absolute paths as observed output. Those paths do not become new source-of-truth values. Report generators should include snapshot metadata and should read roots, projections, and protocol paths from `workspace_manifest.yaml`.

## Delivery Paths

External deliverables produced by workspace tasks resolve through
`workspace_manifest.yaml -> output_roots.workspace`. They are not source,
reports-as-snapshots, or temporary staging. See
`shared/delivery_output_policy.md` for classification and layout.
