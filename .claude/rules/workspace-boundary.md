# Workspace Boundary

This Claude Code project is a governed skill workspace, not a general business-project container.

- Resolve a registered workspace task before broad discovery or modification.
- Do not create a new top-level business project or agent-named project directory.
- The CNN repository is external. If the user requests CNN work, stop and launch it with `claude-project cnn`.
- `${SCRATCH_ROOT}` is external. If the user requests ztemp work, stop and launch it with `claude-project ztemp`.
- Running `claude` directly after changing the terminal directory to an external
  Git root is also valid. Repository switching must happen before Claude starts,
  not by changing directories inside an existing workspace session.
- Default writes must stay inside this Git root and inside an allowed workspace layer.
- Platform loading surfaces, external repositories, and `${DATA_ROOT}` are not writable source layers unless the task explicitly authorizes them.
- If native `Edit` or `Write` is blocked because the target belongs to another
  repository, stop and restart Claude in that repository. Do not fall back to
  PowerShell, Python, redirection, or whole-file string replacement as a bypass.
- If the current request conflicts with this boundary, report the current Git root before acting.
