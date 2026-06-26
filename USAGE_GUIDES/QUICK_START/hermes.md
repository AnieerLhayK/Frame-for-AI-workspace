# Hermes

Hermes loads active skills from:

```text
workspace_manifest.yaml -> platform_roots.hermes
```

The character-system skills intended for Hermes are:

- `style-doctor`: diagnose character output drift without applying patches.
- `zyc`: provide user-facing ZYC-inspired runtime writing and discussion.

Verify discovery with:

```powershell
hermes skills list
```

After changing manifest projections, deploy them from an unrestricted local
PowerShell session:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\setup_links.ps1
```

Hermes may need a new session or a skill reload after deployment. Platform
discovery does not grant either skill authority beyond its manifest and
`SKILL.md` contract.
