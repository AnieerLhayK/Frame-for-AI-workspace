# Shared Workspace Rules

`shared/` contains reusable workspace governance and protocol surfaces. These
files are source material, not generated reports. The manifest and package
protocol manifests remain the source of truth for registration and ownership.

## Layout

- `governance/`: agent identity, authority, registration, and Git integration.
- `workspace/`: workspace policy, path resolution, discovery, failure handling,
  and portability.
- `operations/`: reporting, delivery output, and session continuity.
- `packages/` (under `shared/`): package ownership indexes only. Package protocol content remains in
  each package's canonical `packages/<package-id>/shared/` directory.
- `schemas/`: workspace-level reusable schemas.
- `templates/`: workspace-level reusable request and registration templates.
- `claude/`: optional Claude Code policy library.

Read `INDEX.md` for the protocol index. Read
`packages/character-system/README.md` to understand the package-local shared
protocol boundary.
