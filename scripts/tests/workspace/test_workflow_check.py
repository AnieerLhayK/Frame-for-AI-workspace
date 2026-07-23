from __future__ import annotations

import subprocess
import unittest
from unittest.mock import patch

from scripts.workflow_check import check_workflow


class WorkflowCheckTests(unittest.TestCase):
    def test_active_record_is_added_as_a_narrow_scope_exception(self) -> None:
        task = {"context": {"validation": [], "write_scope": ["scripts/demo.py"]}}
        verification = {
            "errors": [],
            "warnings": [],
            "actual_changes": [],
            "branch": "main",
            "risk_level": "normal",
            "risk_reasons": [],
            "affected_surfaces": [],
            "confirmation_required": False,
            "worktree_recommended": False,
            "recommended_next_steps": [],
        }
        with (
            patch("scripts.workflow_check.resolve_task", return_value=task),
            patch("scripts.workflow_check.active_registration", return_value={
                "task_id": "TASK-20260715-001",
                "operation": "workspace_write",
                "path": "PROJECT_CONTEXT/tasks/records/2026/07/15/TASK-20260715-001.json",
                "status": "active",
            }),
            patch("scripts.workflow_check.verify_changes", return_value=verification) as verify,
        ):
            result = check_workflow(
                "demo",
                [],
                record_id="TASK-20260715-001",
                command_runner=lambda _: subprocess.CompletedProcess([], 0, "", ""),
            )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            verify.call_args.kwargs["additional_write_scope"],
            ["PROJECT_CONTEXT/tasks/records/2026/07/15/TASK-20260715-001.json"],
        )

    def test_missing_record_is_an_error(self) -> None:
        task = {"context": {"validation": [], "write_scope": ["scripts/demo.py"]}}
        verification = {
            "errors": [],
            "warnings": [],
            "actual_changes": [],
            "branch": "main",
            "risk_level": "normal",
            "risk_reasons": [],
            "affected_surfaces": [],
            "confirmation_required": False,
            "worktree_recommended": False,
            "recommended_next_steps": [],
        }
        with (
            patch("scripts.workflow_check.resolve_task", return_value=task),
            patch("scripts.workflow_check.verify_changes", return_value=verification),
        ):
            result = check_workflow(
                "demo",
                [],
                command_runner=lambda _: subprocess.CompletedProcess([], 0, "", ""),
            )
        self.assertEqual(result["status"], "ERROR")
        self.assertIn("--record-id", result["errors"][0])


if __name__ == "__main__":
    unittest.main()
