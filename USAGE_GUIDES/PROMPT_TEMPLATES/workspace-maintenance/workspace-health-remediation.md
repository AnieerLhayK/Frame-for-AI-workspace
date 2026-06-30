# Workspace Health Remediation

Use this prompt when `workspace health` reports NEEDS_ATTENTION or FAIL and the
next step should be source-backed diagnosis rather than guesswork.

```text
Task:
Diagnose and remediate the current `workspace health` output.

Start:
1. Run `workspace health`.
2. If reports are stale, run `workspace reports status --strict` before changing source.
3. Select the smallest matching task id with `workspace task list` or
   `python scripts/resolve_task_context.py --list`.
4. Resolve that task before editing.

Guardrails:
- Do not manually edit generated report conclusions.
- Do not refresh reports until source changes or stale-report evidence justifies it.
- Do not treat skipped tests as failures; explain why they were skipped.
- Keep health text rendering, source behavior, and report snapshots separate.
- Do not change external tools, model settings, provider credentials, or platform
  configuration unless the resolved task explicitly owns that surface.
- Preserve existing user changes and do not commit unless explicitly asked.

Expected output:
- State which health groups are failing or stale.
- Name the source files or report generators that own the failure.
- Propose the smallest remediation path and validation commands.
- Say whether WORKSPACE_ENGINEERING writeback is applicable.
```
