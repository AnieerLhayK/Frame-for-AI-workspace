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

From the Workspace root, use the manifest-bound read-only inventory:

```powershell
python -B -m scripts.platform.hermes_skill_inventory
```

This probe targets the existing Windows `venv/Scripts/python.exe` layout. It
requires an installation declared at `runtime_roots.hermes` and
the skills root at `platform_roots.hermes`; missing declarations stop the probe.
It invokes the installed Python directly, fixes `HERMES_HOME` from the declared
skills root and the platform to `cli`, and compares CLI-list names with enabled
native-loader names in one process. It reports missing registered skills,
name differences, source fingerprints and counts. Python audit hooks deny supported file mutations, process execution and
network operations inside the probe (null-device logging is allowed); missing runtime or hub
metadata stops the query instead of initializing it. This is a diagnostic guard for the reviewed installed functions, not an OS
sandbox for arbitrary or untrusted code. It does not run a model,
reload the gateway or enter the `hermes.exe` update/bootstrap path.

The current fixed-context comparison is 69/69 with no name differences and all
four registered skills present. The previous separate CLI/loader observations
were 68/69, without the CLI name list or matching context; their historical
single-skill difference cannot be reconstructed. This does not establish what
an already-running gateway session sees.

For normal interactive maintenance, `hermes skills list` remains the vendor
entrypoint. Its executable can enter update/bootstrap before listing; do not
use it for an audit that forbids initialization or bypass an updater lock.

## Deploy registered projections

After an authorized manifest projection change, run from the Workspace root in
an unrestricted local PowerShell session:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\platform\setup_links.ps1
```

This command writes registered projections. Inspect the manifest and task scope
before running it. Hermes may need a new session or skill reload after deployment.
Discovery does not grant authority beyond each manifest entry and `SKILL.md`.
