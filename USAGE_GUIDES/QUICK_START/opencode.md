# OpenCode Quick Start

OpenCode discovers active skills through its `/skills` surface. The registered root is `workspace_manifest.yaml -> platform_roots.opencode`; source and authority remain defined by the manifest and each source `SKILL.md`.

Check discovery with:

```powershell
opencode debug paths
opencode debug skill --pure
opencode debug agent build --pure
opencode debug agent zyc_chat --pure
```

`debug skill` inventories candidates from native OpenCode roots and compatible
Claude roots. It can still list skills denied to an agent; a count alone does
not prove agent access. `--pure` excludes external plugins for this diagnostic
invocation, so it does not establish plugin-enhanced session behavior.

In this private Workspace, `opencode.json -> permission.skill` denies `*` and explicitly allows
the five manifest-registered OpenCode skill IDs, plus built-in
`customize-opencode` and existing local `cpp-code-review`. The other compatible
Claude skills, including the unregistered `zf-style` draft, are denied in this
Workspace. Their source files and Claude availability are preserved. When adding
a registered OpenCode skill, update the project allowlist in the same change;
keep built-in/local exceptions explicit and check agent-specific overrides with
`debug agent`. These commands inspect a fresh CLI process; they do not verify
that an already-running session has reloaded the project configuration.
Permission rules use the last matching rule. The public Frame projection omits
the host-specific `opencode.json` and skill payloads; adopters must configure
their own skill allowlist rather than assume these seven entries are installed.

Confirm the intended skills appear in `/skills`, then reload the skill list or start a new session after exposure changes. Use the registered source tree for edits; never edit through projection links. Visibility does not widen skill authority.

## Workspace plugin

The tracked governance plugin source is `.opencode/plugins/workspace-governance.js`. Local npm state under `.opencode/` is runtime support and stays ignored; do not add a blanket `.opencode/` rule to the root ignore file. From `.opencode/`, `npm outdated` checks local package drift.
