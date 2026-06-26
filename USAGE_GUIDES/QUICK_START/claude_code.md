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
