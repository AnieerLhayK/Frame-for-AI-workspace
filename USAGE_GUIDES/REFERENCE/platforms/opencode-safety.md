# OpenCode Loading Safety Notes

These notes cover OpenCode-specific discovery and projection behavior. Skill
authority remains defined by the manifest and source skill.

- Use `/skills` to confirm which skills are actually visible.
- Do not use `style-doctor` as a patch applier.
- Do not let `style-doctor` update patch ledgers or mark maintainer decisions.
- Do not add new platform exposures without checking the skill's role, authority, and intended execution modes.
- Do not edit source through platform projection folders.
- ZYC-specific lessons require review before generator generalization.

## Local Plugin Install Boundary

The workspace tracks the OpenCode governance plugin source at:

```text
.opencode/plugins/workspace-governance.js
```

Local npm install files under `.opencode/` are runtime support, not workspace
source. The `.opencode/.gitignore` intentionally ignores `node_modules`,
`package.json`, `package-lock.json`, `bun.lock`, and `.gitignore` itself.

Do not add a blanket `.opencode/` rule to the root `.gitignore` without first
checking the tracked plugin file. A blanket rule would obscure the distinction
between the governance plugin source and local package-manager state.

When investigating OpenCode package drift, run the check inside `.opencode/`:

```powershell
npm outdated
```

Treat package updates as platform maintenance. They should not change skill
authority, projection ownership, or workspace write scopes.
