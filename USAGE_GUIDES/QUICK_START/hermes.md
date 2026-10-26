# Hermes

Hermes loads registered Workspace skills from
`workspace_manifest.yaml -> platform_roots.hermes`. Determine the current set
from manifest skill exposures and their Hermes projections; the root also
contains Hermes built-in, hub and other local skills.

This private Workspace currently registers the following set. The public Frame
projection omits these skill payloads; template adopters register their own set:

- `style-doctor`: diagnose character output drift without applying patches.
- `zyc`: provide user-facing ZYC-inspired runtime writing and discussion.
- `speaking-like-a-man`: provide its registered writing workflow.
- `cover-it`: provide its registered cover workflow.

## Verify discovery

```powershell
hermes skills list
```

The executable can enter its update/bootstrap path before listing skills.
Use this command only when local runtime initialization is acceptable; stop on
maintenance prompts or failures rather than bypassing updater locks. A directory
or CLI listing does not establish what an already-running gateway session sees.
Compare names and resolved sources with the manifest, keeping built-in, hub and
other local skills separate. The earlier CLI/direct-loader count discrepancy is
an open audit finding, not evidence that the four projections are missing.

## Deploy registered projections

After an authorized manifest projection change, run from the Workspace root in
an unrestricted local PowerShell session:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\platform\setup_links.ps1
```

This command writes registered projections. Inspect the manifest and task scope
before running it. Hermes may need a new session or skill reload after deployment.
Discovery does not grant authority beyond each manifest entry and `SKILL.md`.
