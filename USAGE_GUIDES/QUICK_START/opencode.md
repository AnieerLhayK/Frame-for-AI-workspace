# OpenCode Quick Start

OpenCode discovers active skills through its `/skills` surface. The registered root is `workspace_manifest.yaml -> platform_roots.opencode`; source and authority remain defined by the manifest and each source `SKILL.md`.

Check discovery with:

```powershell
opencode debug paths
opencode debug skill
```

Confirm the intended skills appear in `/skills`, then reload the skill list or start a new session after exposure changes. Use the registered source tree for edits; never edit through projection links. Visibility does not widen skill authority.

## Workspace plugin

The tracked governance plugin source is `.opencode/plugins/workspace-governance.js`. Local npm state under `.opencode/` is runtime support and stays ignored; do not add a blanket `.opencode/` rule to the root ignore file. From `.opencode/`, `npm outdated` checks local package drift.
