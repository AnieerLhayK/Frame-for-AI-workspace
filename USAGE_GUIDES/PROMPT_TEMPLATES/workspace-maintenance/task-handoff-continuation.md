# Task Handoff Continuation

Use this prompt when continuing a previous workspace maintenance thread or
working from a handoff note.

```text
Task:
Continue this workspace maintenance work from the supplied handoff:
<paste handoff or path>

Start:
1. Run `git status --short --branch --untracked-files=all`.
2. Run `git log -5 --oneline --decorate`.
3. Read only the handoff, latest task ledger entries, and resolved task context.
4. Resolve the current task id before editing.

Guardrails:
- Do not assume the handoff is current; compare it with Git state.
- Do not replay old actions that are already merged or superseded.
- Do not read broad reports or archives unless the resolved task needs them.
- Preserve user changes.
- Do not commit or push unless explicitly asked.

Expected output:
- Current branch and cleanliness.
- What the handoff says is done.
- What Git says is actually done.
- The next safe action.
- Whether WORKSPACE_ENGINEERING writeback is applicable.
```
