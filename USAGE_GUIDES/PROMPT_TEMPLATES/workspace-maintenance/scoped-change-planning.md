# Scoped Change Planning

Use this prompt when a maintenance request could plausibly touch more than one
owning layer.

```text
Task:
Plan the smallest safe change surface for this workspace maintenance request:
<paste request>

Start:
1. Run `git status --short --branch --untracked-files=all`.
2. Run `workspace task list` if the task id is not obvious.
3. Resolve the best candidate task id.
4. If multiple owning layers remain plausible, run:
   `workspace changes plan <task-id> --intent <intent> --goal "<goal>"`

Guardrails:
- Do not broaden the task just to make scope verification pass.
- Prefer a split into multiple scoped commits when one request touches multiple
  owning layers.
- Do not move, delete, or clean ignored files unless the user explicitly
  approved cleanup.
- Treat prompt reuse as guidance only; it does not grant write scope.
- Preserve user changes and do not commit unless explicitly asked.

Expected output:
- Recommended task id and why.
- Candidate file groups to change.
- Candidate file groups to avoid.
- Validation commands.
- Whether the task should be split into multiple commits.
```
