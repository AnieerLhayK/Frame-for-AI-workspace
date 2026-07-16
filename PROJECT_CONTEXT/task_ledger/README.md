# Task Ledger

Human-readable maintenance decisions are stored by year, month, and day: `YYYY/MM/DD.md`. The original pre-migration ledger is retained verbatim under `legacy/` so no historical content is lost.

- Read recent entries in the newest day first.
- Use `python scripts/task_ledger.py validate` to check that every archived entry remains discoverable.
- Use `python scripts/task_ledger.py partition` to migrate an existing month file into daily files; never delete `legacy/`.
- Machine-readable outcome facts live separately in `PROJECT_CONTEXT/task_records/YYYY/MM/DD/`.
