# Codex Quick Start

Use Codex for skills currently exposed in the manifest-declared Codex projection.

## Loading

- Skill source and authority: `workspace_manifest.yaml` and each source `SKILL.md`.
- Codex discovery root: `workspace_manifest.yaml -> platform_roots.codex`.
- Workspace source root: `workspace_manifest.yaml -> workspace.source_of_truth`.
- Preferred loading uses the registered projections under `workspace_manifest.yaml -> projections`.

After exposure changes, check `workspace skill list --platform codex` and `workspace validate links`. Open a new session or reload skills if discovery is stale.

## Safety

- Work from the registered source tree; do not edit platform projection links.
- Platform visibility does not grant write authority. Follow the skill's role, authority, execution mode, and active task scope.
- For character generation, use only authorized corpus and keep private corpus material out of Git. Generated characters must remain style-inspired and must not infer private facts or impersonate a person.
