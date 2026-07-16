# Workspace Boundary

This Claude project is a governed skill workspace, not a general business
project container.

- Resolve a registered task before broad discovery or modification.
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
