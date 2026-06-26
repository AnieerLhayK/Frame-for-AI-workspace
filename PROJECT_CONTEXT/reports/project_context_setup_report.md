# Project Context Setup Report

> **Historical snapshot — superseded on 2026-06-14.**
>
> This report records the original PROJECT_CONTEXT setup and intentionally keeps
> its former filenames as historical evidence. It is not a current reading
> guide. Use `ARCHITECTURE.md`, `PROJECT_CONTEXT/README.md`, and
> `PROJECT_CONTEXT/current_status.md` for the current structure.

## 1. New Files

Created:

- `PROJECT_CONTEXT/README.md`
- `PROJECT_CONTEXT/architecture.md`
- `PROJECT_CONTEXT/workspace_purpose.md`
- `PROJECT_CONTEXT/current_status.md`
- `PROJECT_CONTEXT/decisions.md`
- `PROJECT_CONTEXT/todo.md`
- `PROJECT_CONTEXT/bugs.md`
- `PROJECT_CONTEXT/protocols.md`
- `PROJECT_CONTEXT/coding_style.md`
- `PROJECT_CONTEXT/experiment_log.md`
- `PROJECT_CONTEXT/session_handoff.md`
- `PROJECT_CONTEXT/glossary.md`
- `PROJECT_CONTEXT/reports/README.md`
- `PROJECT_CONTEXT/reports/project_context_setup_report.md`

## 2. File Roles

- `README.md`: explains the memory layer and reading order.
- `architecture.md`: maps source root, platform projections, protocols, reports, runtime loop, and context layer.
- `workspace_purpose.md`: defines why the workspace exists, when new skills belong here, and how to propose package/domain or new-workspace alternatives.
- `current_status.md`: summarizes completed governance work, validation results, and open items.
- `decisions.md`: records key project decisions with reasons and consequences.
- `todo.md`: organizes next work into P0, P1, and P2.
- `bugs.md`: tracks known risks and suggested fixes.
- `protocols.md`: indexes shared protocols without copying their content.
- `coding_style.md`: captures script and governance coding conventions.
- `experiment_log.md`: records important validation and governance milestones.
- `session_handoff.md`: gives the next session a direct continuation path.
- `glossary.md`: defines project terms.
- `reports/README.md`: explains context-local summaries.

## 3. Difference From Other Layers

- `workspace_manifest.yaml`: machine-readable source of truth.
- `shared/`: protocol and policy layer.
- `reports/`: generated or historical snapshot layer.
- `reports/runtime_loop/`: event tracking and ledgers for runtime drift.
- `PROJECT_CONTEXT/`: human and agent memory layer.

`PROJECT_CONTEXT/` should summarize and orient. It should not become a registry, validator, runtime ledger, or protocol source.

## 4. New Session Usage

A new Codex or OpenCode session should read:

1. `PROJECT_CONTEXT/README.md`
2. `PROJECT_CONTEXT/current_status.md`
3. `PROJECT_CONTEXT/architecture.md`
4. `PROJECT_CONTEXT/todo.md`
5. `workspace_manifest.yaml`
6. `shared/`

If context conflicts, prefer manifest for paths, shared docs for protocols, current Git state for actual files, and reports only after checking snapshot headers.

## 5. Manual Maintenance Still Needed

- Update `current_status.md` after governance phases.
- Update `decisions.md` when architectural decisions change.
- Update `todo.md` and `bugs.md` as risks are resolved.
- Update `session_handoff.md` before handing work to a new long-running session.
- Keep PROJECT_CONTEXT concise; link to source layers instead of copying them.

## 6. Next Recommendations

- Commit the context layer after review.
- Use `session_handoff.md` at the start of future sessions.
- Add a short context update whenever a governance pass is committed.
- Consider a future script that checks whether PROJECT_CONTEXT references stale report commits, but keep it advisory.

## 7. Suggested Commit Message

```text
Add project context memory layer
```
