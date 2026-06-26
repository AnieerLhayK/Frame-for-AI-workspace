# Architecture Patterns

These patterns are drawn from the current workspace and should be treated as reusable design vocabulary, not universal law.

## Workspace-Driven Ecosystem

- What: one Git-managed workspace coordinates multiple skills, protocols, scripts, reports, and projections.
- Why: shared infrastructure is easier to validate from one source center.
- When useful: several skills share maintenance style, projections, or governance.
- Risks: unrelated domains may be forced together.
- Common mistakes: treating the workspace as one giant agent instead of a governed monorepo.

## Shared Protocol Layer

- What: common behavioral and governance contracts live in `shared/`.
- Why: skills can reference one source instead of copying rules.
- When useful: rules apply across skills or platforms.
- Risks: top-level shared can become a dumping ground.
- Common mistakes: putting domain-specific business logic into global shared protocols.

## Projection Surface

- What: platform directories expose skills to Codex or OpenCode through links or deployment paths.
- Why: runtime tools need platform-specific entry points.
- When useful: source should remain Git-managed while platforms read from their expected roots.
- Risks: users may edit projection directories directly.
- Common mistakes: confusing projection path with source path, role, or authority.

## Independent Skill Contracts

- What: model role, authority, execution mode, and platform exposure as separate dimensions.
- Why: the same source skill can be visible on multiple platforms without receiving broader permissions.
- When useful: a governed monorepo serves multiple agent runtimes.
- Risks: compatibility fields may drift while old consumers are being migrated.
- Common mistakes: inferring write authority from the invoking platform or source directory prefix.

## Runtime Loop

- What: runtime failure moves through diagnosis, handoff, patch, validation, optional generalization, and ledger update.
- Why: skill evolution needs an audit trail.
- When useful: behavior can drift after real use.
- Risks: too much paperwork for trivial fixes.
- Common mistakes: skipping validation or generalizing a one-off patch.

## Validator Layer

- What: scripts check protocol manifests, required files, templates, ledgers, and references.
- Why: enforceable checks reduce document-only drift.
- When useful: cross-file contracts matter.
- Risks: over-strict validators block harmless iteration.
- Common mistakes: making warnings fatal before the project is ready.

## Manifest Governance

- What: `workspace_manifest.yaml` centralizes roots, skills, projections, protocols, discovery, and failure policy.
- Why: path truth should not be scattered.
- When useful: multiple scripts and agents need consistent path resolution.
- Risks: a manifest can still be locally absolute.
- Common mistakes: treating the manifest as magic that never needs migration work.

## Durable Runtime Records

- What: ledgers and notes preserve the history of runtime failures and fixes.
- Why: future maintainers need to know why behavior changed.
- When useful: patches may become generator lessons later.
- Risks: stale ledgers if humans forget updates.
- Common mistakes: writing reports but not linking IDs.

## Source-Of-Truth Architecture

- What: each layer has a clear authority: manifest for paths, shared for protocols, source folders for skill code.
- Why: conflict resolution becomes simpler.
- When useful: agents and humans work across sessions.
- Risks: unclear exception handling.
- Common mistakes: letting reports overrule source files.

## Bootstrap Discovery

- What: tools find the workspace by walking upward from a start path.
- Why: sessions may begin inside a skill folder.
- When useful: local scripts need robust startup.
- Risks: finding a parent workspace that is not intended.
- Common mistakes: unbounded parent traversal.

## Bounded Discovery

- What: discovery is limited by max parent depth and known manifest filename.
- Why: safety and determinism matter more than clever search.
- When useful: portable local tooling.
- Risks: deeply nested launch points may need explicit `--start`.
- Common mistakes: falling back silently to the current directory.

## Migration Dry-Run

- What: simulate root, shared, platform, or drive changes without moving files.
- Why: path breakage should be visible before migration.
- When useful: moving machines, drives, or projection roots.
- Risks: dry-run can miss external platform assumptions.
- Common mistakes: treating a dry-run as an actual migration.

## Platform Separation

- What: Codex and OpenCode can share workspace governance and skill sources while keeping separate platform loading roots.
- Why: each platform has its own skill loading mechanics.
- When useful: one ecosystem targets multiple runtimes.
- Risks: platform-specific behavior leaking into global protocols.
- Common mistakes: assuming one platform's directory rules apply to the other or that exposure implies ownership.
