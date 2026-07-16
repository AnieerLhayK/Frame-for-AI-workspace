# Task Outcome Records

This tracked directory is the machine-readable fact layer for one workspace task. Store one JSON file per task at `YYYY/MM/DD/TASK-*.json`; the schema and compatibility rules live in `schema.json`.

## Required registration for mutations

Before any workspace-source write, or any external write initiated through the workspace, create one active record. Read-only investigation is exempt.

```powershell
$record = (workspace records start --task-type <route> --operation workspace_write --tokens-estimated <count> | ConvertFrom-Json).task_id
$env:WORKSPACE_TASK_RECORD = $record  # needed by Claude/OpenCode write adapters
```

For a task that will also change an approved external target, start it with both declarations instead:

```powershell
$record = (workspace records start --task-type <route> --operation workspace_write --operation external_write | ConvertFrom-Json).task_id
```

`start` allocates the daily ID. Do not use `init` to modify an already-created record; use it only when an integration has already allocated an ID.

Before a write gate, use the same ID:

```powershell
workspace records require $record --operation workspace_write
workspace agent check --agent codex --path scripts/example.py --record-id $record
workspace workflow check <route> --record-id $record
```

For external targets, the record must also declare `external_write`; `workspace agent check` selects that operation from the target path. Run `workflow check` while the record is still `in_progress`, then finalize it after validation:

```powershell
workspace records finalize $record --status successful --validation passed --usability usable --human-edit-rounds 1
```

All records belong in Git: they are durable, reviewable task facts. Do not store provider transcripts, secrets, raw prompts, or volatile tool logs here. Generated charts and periodic reports belong under `reports/` and should be reproducible from these records.

Maintenance priorities are schema compatibility, evidence quality, stable definitions, and daily partitioning. New optional fields may be added under a named object; changing the meaning of an existing field requires a schema-version increment and a migration. Never re-consolidate daily records into a month file.
