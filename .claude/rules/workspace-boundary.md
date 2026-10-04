# Workspace Boundary

This Claude project is a governed skill workspace, not a general business
project container.

- Resolve a registered task before broad discovery or modification.
- Create a TASK owned by `claude` with `--owner-session` matching this session.
  The hook discovers the newest active TASK for that session (or its successful
  TASK during audit closure). `WORKSPACE_TASK_RECORD` is an optional prelaunch
  selection; owner and session must still match. Hook errors show the session ID.
  A Codex TASK cannot be borrowed for a Claude write.
- Maintain ordinary source and records. Core governance, authorization, guards,
  instruction entrypoints and publisher configuration belong to Codex.
- For delivery, use `workspace workflow check` and the Git integration policy.
  A governance batch requires Codex or explicit user approval bound to its exact
  commits; this approval does not permit editing governance. Never self-issue a
  Codex approval or replace a denied edit with a shell write.
- Do not create top-level business projects or agent-named directories.
- CNN and `${SCRATCH_ROOT}` are external. Launch them with `claude-project cnn` or
  `claude-project ztemp`; changing directories inside this session is not a
  project switch.
- Default writes stay inside this Git root and an allowed workspace layer.
  Platform surfaces, external repositories, and `${DATA_ROOT}` are not source
  layers unless explicitly authorized.
- If native `Edit`/`Write` is blocked for another repository, restart Claude
  there. Never bypass the guard with PowerShell, Python, redirection, or whole-
  file replacement.
- On a conflicting request, report the current Git root before acting.
