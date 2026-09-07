from __future__ import annotations

import subprocess
import unittest
from unittest.mock import patch

from scripts.workspace.workflow_check import check_workflow


class WorkflowCheckTests(unittest.TestCase):
    def test_external_record_requires_matching_agent_and_client_root(self) -> None:
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
        external = {
            "task_id": "TASK-20260715-001",
            "operation": "workspace_write",
            "path": "PROJECT_CONTEXT/tasks/records/2026/07/15/TASK-20260715-001.json",
            "status": "active",
            "origin": {
                "kind": "external_workspace",
                "agent": "opencode",
                "client_root": "D:/client",
            },
            "git_baseline": None,
        }
        with (
            patch("scripts.workspace.workflow_check.resolve_task", return_value=task),
            patch("scripts.workspace.workflow_check.active_registration", return_value=external),
            patch("scripts.workspace.workflow_check.active_external_registration", return_value=external) as verify_origin,
            patch("scripts.workspace.workflow_check.verify_changes", return_value=verification),
        ):
            missing = check_workflow(
                "demo",
                [],
                record_id="TASK-20260715-001",
                command_runner=lambda _: subprocess.CompletedProcess([], 0, "", ""),
            )
            matched = check_workflow(
                "demo",
                [],
                record_id="TASK-20260715-001",
                agent_id="opencode",
                external_client_root="D:/client",
                command_runner=lambda _: subprocess.CompletedProcess([], 0, "", ""),
            )
        self.assertEqual(missing["status"], "ERROR")
        self.assertIn("--external-client-root", missing["errors"][0])
        self.assertEqual(matched["status"], "PASS")
        verify_origin.assert_called_once_with(
            "TASK-20260715-001", agent="opencode", client_root="D:/client"
        )

    def test_baselined_workflow_runs_diff_check_only_for_task_paths(self) -> None:
        task = {"context": {"validation": [], "write_scope": ["scripts/"]}}
        baseline = {
            "branch": "main",
            "head_commit": "a" * 40,
            "captured_at": "2026-08-28T00:00:00Z",
            "paths": [],
        }
        registration = {
            "task_id": "TASK-20260715-001",
            "operation": "workspace_write",
            "path": "PROJECT_CONTEXT/tasks/records/2026/07/15/TASK-20260715-001.json",
            "status": "active",
            "git_baseline": baseline,
            "origin": None,
        }
        verification = {
            "errors": [],
            "warnings": [],
            "actual_changes": [{"path": "scripts/demo.py"}],
            "branch": "main",
            "risk_level": "normal",
            "risk_reasons": [],
            "affected_surfaces": [],
            "confirmation_required": False,
            "worktree_recommended": False,
            "recommended_next_steps": [],
        }
        calls: list[list[str]] = []

        def runner(arguments: list[str]) -> subprocess.CompletedProcess[str]:
            calls.append(arguments)
            return subprocess.CompletedProcess([], 0, "", "")

        with (
            patch("scripts.workspace.workflow_check.resolve_task", return_value=task),
            patch("scripts.workspace.workflow_check.active_registration", return_value=registration),
            patch("scripts.workspace.workflow_check.verify_changes", return_value=verification),
        ):
            result = check_workflow(
                "demo", [], record_id="TASK-20260715-001", command_runner=runner
            )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            calls,
            [
                ["git", "diff", "--check", "--", "scripts/demo.py"],
                ["git", "diff", "--cached", "--check", "--", "scripts/demo.py"],
            ],
        )

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
            patch("scripts.workspace.workflow_check.resolve_task", return_value=task),
            patch("scripts.workspace.workflow_check.active_registration", return_value={
                "task_id": "TASK-20260715-001",
                "operation": "workspace_write",
                "path": "PROJECT_CONTEXT/tasks/records/2026/07/15/TASK-20260715-001.json",
                "status": "active",
            }),
            patch("scripts.workspace.workflow_check.verify_changes", return_value=verification) as verify,
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
            patch("scripts.workspace.workflow_check.resolve_task", return_value=task),
            patch("scripts.workspace.workflow_check.verify_changes", return_value=verification),
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
