# Claude Code Project Switching

Claude Code uses the directory where it starts as its project root. It does not
choose a project from `workspace_manifest.yaml`.

You may start it directly from any governed project root:

```powershell
cd ${OTHER_PROJECT_ROOT}/source/repos/CNN
claude
```

This is fully supported. The named launchers below are conveniences, not a
requirement.

## Start In The Skill Workspace

```powershell
claude-workspace
```

This opens the Git root registered for the `workspace` alias, loads its tracked
`CLAUDE.md` and `.claude/` boundary rules, and treats the repository as a
governed skill workspace.

Do not create unrelated business projects inside this workspace.

## Model Advice Switch

The workspace can ask Claude Code to assess whether a task is safe for the
default model or should use `deepseek-v4-pro`. Use the workspace CLI:

```powershell
workspace claude model-advice status
workspace claude model-advice on
workspace claude model-advice off
```

The tracked default switch file is:

```text
${WORKSPACE_ROOT}\.claude\model-routing-advice.json
```

The machine-local override is:

```text
${WORKSPACE_ROOT}\.claude\model-routing-advice.local.json
```

The local override is ignored by Git and wins over the tracked default.

Default state:

```json
{
  "interface_version": 1,
  "enabled": true,
  "mode": "advisory_pause"
}
```

`workspace claude model-advice off` writes the local override with
`"enabled": false`. When disabled, Claude Code should not print model-tier
assessments, the hook will not inject routing context, and the hook will not
pause or block tool use for model advice. This does not change the active model,
LiteLLM, provider credentials, plugins, permissions, or Git rules.

`workspace claude model-advice on` writes the local override with
`"enabled": true` and restores the visible assessment and Pro pause behavior.
Use `--scope tracked` only when intentionally changing the repository default.

`status` reports both layers:

- `hook injection/enforcement`: whether the Claude hook will inject or block.
- `static CLAUDE.md prompt layer`: whether static project instructions still
  contain routing templates.
- `Fully off`: `yes` only when the effective toggle is OFF, the hook is silent,
  and `CLAUDE.md` has no static routing template.

For another Claude Code project, use the same interface with an explicit root:

```powershell
workspace claude model-advice status --project-root D:\path\to\project
workspace claude model-advice on --project-root D:\path\to\project
workspace claude model-advice off --project-root D:\path\to\project
```

The CLI can create or update that project's toggle file, but a project also
needs its own `.claude/settings.json` hook, model-routing hook script,
and `CLAUDE.md` rule before the switch affects Claude Code behavior. Do not
statically import the detailed routing policy from `CLAUDE.md`; the hook should
inject the detailed policy only when the toggle is ON. `status` reports those
integration checks explicitly.

## Start In The CNN Project

```powershell
claude-cnn
```

This opens the separately versioned CNN repository and loads that repository's
own instructions and write guard.

## Start In The ztemp Project

```powershell
claude-ztemp
```

This opens the separately versioned ztemp repository and loads that repository's
own instructions and write guard.

## Generic Project Command

```powershell
claude-project workspace
claude-project cnn
claude-project ztemp
```

Additional Claude arguments may follow the project alias:

```powershell
claude-project cnn --continue
```

The machine-local alias registry is:

```text
<claude-data-root>\project_roots.json
```

The launcher refuses missing directories, non-Git directories, and registered
paths that are not the actual Git root.

## Important Difference

- `workspace_manifest.yaml` governs workspace skills and platform projections.
- `.claude/` governs Claude Code behavior inside one Git repository.
- `project_roots.json` maps local launcher aliases to separate Git roots.

An external project should not be added to the workspace manifest merely to
make Claude Code discover it.

## Do Not Switch Repositories Inside A Running Session

Changing directories inside an existing Claude session does not turn that
session into a different Claude project. Its `CLAUDE_PROJECT_DIR`, instructions,
hooks, and memory still belong to the repository where Claude started.

If `Edit` or `Write` reports a project-boundary error:

1. Stop the current Claude session.
2. Open a terminal in the intended Git root.
3. Run `claude`, or use `claude-project <alias>`.
4. Confirm the reported Git root before editing.

Do not work around a blocked native editor with PowerShell string replacement,
Python file rewriting, shell redirection, or another indirect write command.
That bypasses project instructions and is especially risky for Markdown tables,
code fences, line endings, and non-ASCII text.

## Long-Task Completion Notifications

This workspace keeps a managed repair kit for user-level Claude Code completion
notifications in:

```text
scripts\claude_long_task_notifications\
scripts\install_claude_long_task_notifications.ps1
```

The repair uses `UserPromptSubmit` to record a per-session start time and `Stop`
to notify after the main Claude Code agent finishes responding. Tasks that run
for at least 5 minutes show a Windows tray notification. Tasks that run for at
least 10 minutes also call Hermes `messages_send`; the default target is
`qqbot`, which sends to the configured QQBot home channel.

If a long task emits internal task-notification prompts before the final Stop
event, the start hook preserves the existing per-session start state instead of
resetting the clock. State older than 24 hours is treated as stale and may be
overwritten.

Preview the installation without touching user settings:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File scripts\install_claude_long_task_notifications.ps1
```

Install or refresh the user-level hooks:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File scripts\install_claude_long_task_notifications.ps1 `
  -Apply `
  -Target qqbot
```

The installer copies the managed scripts to `%USERPROFILE%\.claude\hooks`,
backs up `%USERPROFILE%\.claude\settings.json`, and updates only notification
entries under `UserPromptSubmit` and `Stop`. Other hook entries are preserved.

Runtime diagnostics are written to:

```text
%TEMP%\claude-code-notifications\hook-events.log
%TEMP%\claude-code-notifications\hermes-mcp-client.log
```

Check `hook-events.log` first. It records whether the start state was written,
whether `Stop` found that state, the calculated duration, and whether Hermes
was invoked.
