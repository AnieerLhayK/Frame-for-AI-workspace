# Agent Change Requests

This directory is the review inbox for agents that do not hold the capability
needed to modify a requested workspace surface.

Requests are governance records, not generated report snapshots and not
authorization. Codex, Claude Code, or the user must review each request before
structural work begins.

Generate a request with:

```powershell
workspace agent request --agent hermes --mode worktree `
  --summary "Register a missing skill exposure" `
  --path workspace_manifest.yaml
```

Do not place lease files here. Temporary leases are external runtime state.
