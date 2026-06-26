# Hermes Workspace Integration Plan

Generated: 2026-06-08

Workspace root: `${WORKSPACE_ROOT}`

## Post-Action Status

After user approval, `terminal.cwd` was set to `${WORKSPACE_ROOT}` in `${DATA_ROOT}/hermes\config.yaml`.

Backup created before the change:

```text
D:\Backup\migration\hermes-config-before-workspace-cwd-20260608_191049.yaml
```

Hermes gateway was restarted successfully after the change:

- Previous gateway stopped cleanly.
- New gateway started via scheduled task `Hermes_Gateway`.
- New PID: `32488`.

## Current Evidence

Hermes session history shows a CLI session started with:

- `cwd`: `${WORKSPACE_ROOT}`
- Project context loaded from `AGENTS.md`
- Project context included `PROJECT_CONTEXT/` and `workspace_manifest.yaml`

This proves Hermes can run inside the workspace and load its local context when started from that directory.

Current config:

- `terminal.cwd`: `.`

Interpretation:

- Hermes' working directory is relative to the process start directory.
- If the gateway service is started from `${WORKSPACE_ROOT}`, terminal/file/code tools will naturally operate there.
- If the gateway is started from `${DATA_ROOT}/hermes\hermes-agent` or another path, remote commands may not start in the workspace.

## Workspace Assets Hermes Can Use

### `PROJECT_CONTEXT`

Status: usable.

Role:

- Long-term workspace memory.
- Task routing and context budget.
- Maintenance handoff.

Hermes already loaded this layer in a prior CLI session. For remote tasks, Hermes should be prompted or configured to start from `${WORKSPACE_ROOT}` so these files are auto-injected by AGENTS/project context rules.

### `workspace_manifest.yaml`

Status: usable.

Role:

- Machine-readable source of truth for workspace root, platform roots, skill projections, protocols, portability policy.

Hermes can read it with file or terminal tools. It should be treated as stronger than old reports.

### `skills`

Status: partially usable, with boundary.

Hermes has its own skill system under `${DATA_ROOT}/hermes\skills` and bundled/optional skills under `${DATA_ROOT}/hermes\hermes-agent`.

The workspace contains Codex/OpenCode skill sources. These are not automatically Hermes skills. Hermes can inspect and edit them as repository files, but should not assume they are installed into Hermes runtime unless deliberately projected or installed.

Plan:

- Keep workspace skill sources as repo source of truth.
- Do not directly copy them into Hermes skills by default.
- If Hermes needs a dedicated workspace-control skill, create a small Hermes skill that points to `${WORKSPACE_ROOT}` and the manifest rules.

### `reports`

Status: usable.

Role:

- Generated snapshots and diagnosis records.
- Suitable place for Hermes diagnostics such as this report set.

Plan:

- Continue storing Hermes diagnostics in `${WORKSPACE_ROOT}\reports\hermes`.
- Do not store Hermes runtime caches, logs, tokens, or state DB in Git.

### `automation`

Status: no top-level `${WORKSPACE_ROOT}\automation` directory found during inspection.

Hermes has its own automation surfaces:

- `cron`
- `kanban`
- `gateway`
- `sessions`

Plan:

- If workspace-level automation is needed, define it explicitly as a source-controlled plan/config layer.
- Keep actual Hermes runtime jobs and state in `${DATA_ROOT}/hermes`.

## Recommended Integration Shape

```text
QQ / Weixin
  -> Hermes gateway
  -> Hermes session starts in ${WORKSPACE_ROOT}
  -> Reads AGENTS.md + PROJECT_CONTEXT + workspace_manifest.yaml
  -> Uses terminal/file/code_execution against workspace
  -> Optionally delegates to Codex / Claude Code / OpenCode CLI
  -> Returns result through messaging adapter
```

## Required Configuration Change

Hermes' stable workspace behavior has now been set through `terminal.cwd`.

Alternative routes remain available if this needs to be changed later:

Option A: start gateway from workspace.

```powershell
Set-Location ${WORKSPACE_ROOT}
hermes gateway run
```

Option B: change `terminal.cwd` from `.` to `${WORKSPACE_ROOT}`.

```yaml
terminal:
  cwd: ${WORKSPACE_ROOT}
```

Option C: create a dedicated Hermes profile for workspace automation.

Use when you want separate model/tool/prompt policy for long-running remote control.

## Next Integration Tasks

1. Add a small Hermes workspace-control skill or SOUL/persona note that says: use `workspace_manifest.yaml`, obey `PROJECT_CONTEXT/context_budget.md`, and write reports under `reports/`.
2. Configure delegation policy for Codex/Claude Code/OpenCode only after deciding which agent owns which task type.
3. Add a low-risk remote command test through QQ: ask Hermes to create a timestamped file under `${WORKSPACE_ROOT}\reports\hermes\probe`.
4. Keep Hermes state/logs/tokens in `${DATA_ROOT}/hermes`; keep only reports/config snapshots in Git.
5. Re-run Weixin inbound pairing test from phone; local evidence is still missing for that path.
