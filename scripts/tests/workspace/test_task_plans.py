from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.workspace import task_ledger, task_plans, task_records


class TaskPlansTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = "2026-09-01T00:00:03Z"
        clock = patch.object(task_plans, "timestamp", side_effect=lambda value=None: value or self.now)
        self.clock = clock.start()
        self.addCleanup(clock.stop)

    def _create(self, root: Path, *, title: str = "Plan", depends_on: list[str] | None = None) -> dict:
        args = SimpleNamespace(title=title, kind="ticket", description="A bounded change.", acceptance_criterion=["It works"], depends_on=depends_on or [], source_ref=[], created_at="2026-09-01T00:00:00Z")
        return task_plans.create_plan(args)

    def test_plan_lifecycle_requires_completed_dependencies_and_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(task_plans, "RECORD_ROOT", Path(directory)):
            parent = self._create(Path(directory), title="Parent")
            child = self._create(Path(directory), title="Child", depends_on=[parent["plan_id"]])
            with self.assertRaisesRegex(ValueError, "dependency"):
                task_plans.set_plan_status(SimpleNamespace(plan_id=child["plan_id"], status="ready", updated_at="2026-09-01T00:00:01Z"))
            task_plans.set_plan_status(SimpleNamespace(plan_id=parent["plan_id"], status="ready", updated_at="2026-09-01T00:00:01Z"))
            task_plans.claim_plan(SimpleNamespace(plan_id=parent["plan_id"], actor="codex", hours=24, now="2026-09-01T00:00:02Z"))
            task_plans.link_execution(parent["plan_id"], "TASK-20260901-001")
            task_plans.record_execution_outcome(parent["plan_id"], "TASK-20260901-001", "successful")
            task_plans.set_plan_status(SimpleNamespace(plan_id=child["plan_id"], status="ready", updated_at="2026-09-01T00:00:03Z"))
            claimed = task_plans.claim_plan(SimpleNamespace(plan_id=child["plan_id"], actor="claude", hours=24, now="2026-09-01T00:00:04Z"))
        self.assertEqual(claimed["status"], "claimed")

    def test_claim_expires_and_can_be_taken_over(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(task_plans, "RECORD_ROOT", Path(directory)):
            plan = self._create(Path(directory))
            task_plans.set_plan_status(SimpleNamespace(plan_id=plan["plan_id"], status="ready", updated_at="2026-09-01T00:00:01Z"))
            task_plans.claim_plan(SimpleNamespace(plan_id=plan["plan_id"], actor="first", hours=24, now="2026-09-01T00:00:02Z"))
            claimed = task_plans.claim_plan(SimpleNamespace(plan_id=plan["plan_id"], actor="second", hours=24, now="2026-09-02T00:00:03Z"))
        self.assertEqual(claimed["claim"]["actor"], "second")

    def test_claim_duration_must_be_positive(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(task_plans, "RECORD_ROOT", Path(directory)):
            plan = self._create(Path(directory))
            task_plans.set_plan_status(SimpleNamespace(plan_id=plan["plan_id"], status="ready", updated_at="2026-09-01T00:00:01Z"))
            with self.assertRaisesRegex(ValueError, "positive"):
                task_plans.claim_plan(SimpleNamespace(plan_id=plan["plan_id"], actor="codex", hours=0, now="2026-09-01T00:00:02Z"))

    def test_expired_claim_cannot_start_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(task_plans, "RECORD_ROOT", Path(directory)):
            plan = self._create(Path(directory))
            task_plans.set_plan_status(SimpleNamespace(plan_id=plan["plan_id"], status="ready", updated_at="2026-09-01T00:00:01Z"))
            task_plans.claim_plan(SimpleNamespace(plan_id=plan["plan_id"], actor="codex", hours=24, now="2026-09-01T00:00:02Z"))
            self.now = "2026-09-02T00:00:02Z"
            with self.assertRaisesRegex(ValueError, "expired"):
                task_plans.link_execution(plan["plan_id"], "TASK-20260901-001")
            _, unchanged = task_plans.read_plan(plan["plan_id"])
            self.assertEqual(unchanged["execution_task_ids"], [])

    def test_validation_rejects_dependency_cycles_and_map_missing_plans(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(task_plans, "RECORD_ROOT", Path(directory)):
            plan = self._create(Path(directory))
            path, payload = task_plans.read_plan(plan["plan_id"])
            payload["depends_on"] = [plan["plan_id"]]
            task_plans.write(path, payload)
            result = task_plans.validate_all()
        self.assertFalse(result["valid"])
        self.assertIn(plan["plan_id"], result["failures"])

    def test_mutation_gate_uses_an_active_workspace_write_record(self) -> None:
        with patch("scripts.workspace.task_records.active_registration") as registration:
            task_plans.require_write_authorization("TASK-20260901-001")
        registration.assert_called_once_with("TASK-20260901-001", "workspace_write")

    def test_task_start_and_successful_finalize_link_the_claimed_plan(self) -> None:
        baseline = {"branch": "codex/test", "head_commit": "a" * 40, "captured_at": "2026-09-01T00:00:00Z", "paths": []}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(task_plans, "RECORD_ROOT", root / "records"), patch.object(task_records, "RECORD_ROOT", root / "records"), patch.object(task_ledger, "DESTINATION", root / "ledger"), patch.object(task_records, "capture_git_baseline", return_value=baseline):
                plan = self._create(root)
                task_plans.set_plan_status(SimpleNamespace(plan_id=plan["plan_id"], status="ready", updated_at="2026-09-01T00:00:01Z"))
                task_plans.claim_plan(SimpleNamespace(plan_id=plan["plan_id"], actor="codex", hours=24, now="2026-09-01T00:00:02Z"))
                task = task_records.start(SimpleNamespace(task_type="demo", tokens_estimated=1, bind=[], operation=["workspace_write"], started_at="2026-09-01T00:00:03Z", owner_agent=None, owner_session=None, plan_id=plan["plan_id"]))
                _, linked = task_plans.read_plan(plan["plan_id"])
                self.assertEqual(linked["status"], "in_progress")
                self.assertEqual(linked["execution_task_ids"], [task["task_id"]])
                task_records.finalize(SimpleNamespace(task_id=task["task_id"], ended_at="2026-09-01T00:00:04Z", status="successful", validation="passed", usability="usable", human_edit_rounds=0, command=[], tokens_actual=None, tokens_saved=None, currency_cost=None))
                _, completed = task_plans.read_plan(plan["plan_id"])
        self.assertEqual(completed["status"], "completed")


if __name__ == "__main__":
    unittest.main()
