from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import task_records


class TaskRecordsTests(unittest.TestCase):
    def test_validate_rejects_success_without_validation(self) -> None:
        record = {"schema_version": "1.0", "task_id": "TASK-20260715-001", "started_at": "2026-07-15T00:00:00Z", "status": "successful", "validation": {"status": "not_run"}, "human_edit_rounds": 0, "tokens": {"estimated": 1, "actual": None, "saved": None}, "usability": {"status": "usable"}}
        self.assertIn("successful records require validation", task_records.validate_record(record))

    def test_record_path_is_year_month_day_partitioned(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(task_records, "RECORD_ROOT", Path(directory)):
            path = task_records.record_path("TASK-20260715-001", "2026-07-15T00:00:00Z")
        self.assertEqual(path.parts[-4:], ("2026", "07", "15", "TASK-20260715-001.json"))

    def test_active_registration_requires_declared_operation(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            task_records, "RECORD_ROOT", Path(directory)
        ):
            record = task_records.initial_record(
                "TASK-20260715-001",
                task_type="demo",
                started_at="2026-07-15T00:00:00Z",
                tokens_estimated=0,
                operations=["workspace_write"],
            )
            path = task_records.record_path(record["task_id"], record["started_at"])
            task_records.create_record(path, record)
            active = task_records.active_registration(
                "TASK-20260715-001", "workspace_write"
            )
            self.assertEqual(active["status"], "active")
            with self.assertRaisesRegex(ValueError, "external_write"):
                task_records.active_registration(
                    "TASK-20260715-001", "external_write"
                )

    def test_active_registration_rejects_historical_unregistered_record(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            task_records, "RECORD_ROOT", Path(directory)
        ):
            record = {
                "schema_version": "1.0",
                "task_id": "TASK-20260715-001",
                "started_at": "2026-07-15T00:00:00Z",
                "status": "in_progress",
                "validation": {"status": "not_run"},
                "human_edit_rounds": 0,
                "tokens": {"estimated": 0, "actual": None, "saved": None},
                "usability": {"status": "unknown"},
            }
            path = task_records.record_path(record["task_id"], record["started_at"])
            task_records.create_record(path, record)
            with self.assertRaisesRegex(ValueError, "not registered"):
                task_records.active_registration(
                    "TASK-20260715-001", "workspace_write"
                )


if __name__ == "__main__":
    unittest.main()
