# Delivery Output Policy

This policy keeps external AI deliverables separate from durable workspace
source and transient tool files.

## Three Storage Classes

| Class | Destination | Examples |
| --- | --- | --- |
| Repository-native artifact | Owning workspace source path | Skill source, tests, fixtures, tracked reports, runtime-loop records, policies |
| Transient working file | `AI_TOOL_STAGING_DIR` or tool staging | Screenshots, conversions, probes, temporary downloads, debug dumps |
| External deliverable | `workspace_manifest.yaml -> output_roots.workspace` | Documents, images, export bundles, and reports intended for use outside Git |

Classify by purpose, not file extension. A Markdown governance report tracked by
the repository is repository-native; a Markdown summary delivered to the user
outside the repository is an external deliverable.

## External Layout

Resolve the root from the manifest, then use:

```text
<workspace-output-root>/
  deliverables/
    <YYYY-MM>/
      <task-id-or-slug>/
  exports/
    <YYYY-MM>/
      <task-id-or-slug>/
  external-reports/
    <YYYY-MM>/
      <task-id-or-slug>/
```

- `deliverables/`: final documents, images, media, or other user-facing files.
- `exports/`: portable bundles, archives, converted copies, and handoff packages.
- `external-reports/`: audits or summaries intended outside workspace governance.

Use lowercase ASCII kebab-case for a task slug. Reuse a registered task id when
one exists. A task directory may be omitted for a single unambiguous file, but
month and category must remain.

## Routing Rules

1. Keep files required to build, test, validate, or maintain the repository in
   their owning source paths.
2. Keep intermediate files in staging and delete them after successful use.
3. Put only final external-facing outputs under the manifest-declared output
   root.
4. If the user explicitly names another destination, that instruction overrides
   the default output root for that deliverable.
5. Do not place credentials, private corpus material, raw session databases, or
   unredacted sensitive data in the output root.
6. Do not duplicate a deliverable in both workspace source and the output root
   unless one copy is an intentional tracked source artifact.
7. Final responses should link to the resulting absolute output path.

Creating an external deliverable does not grant authority to modify workspace
source, platform projections, or governance structure.

## Existing Files

This policy applies prospectively. Existing files directly under the broader
output directory are not automatically moved or renamed. Migrate them only as
a separate, reviewed cleanup task.
