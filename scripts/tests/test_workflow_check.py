from __future__ import annotations

import subprocess
import unittest
from unittest.mock import patch

from scripts.workflow_check import check_workflow


def completed(returncode: int = 0, stdout: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], returncode, stdout, "")


TASK = {
    "status": "PASS",
    "task": {"id": "demo"},
    "context": {
        "write_scope": ["scripts/"],
        "validation": ["python -m unittest scripts.tests.test_demo"],
    },
}


class WorkflowCheckTests(unittest.TestCase):
    def test_pass_matches_scope_verifier_and_lists_validation(self) -> None:
        verification = {
            "status": "PASS",
            "branch": "codex/demo",
            "risk_level": "normal",
            "confirmation_required": False,
            "worktree_recommended": False,
            "actual_changes": [{"path": "scripts/demo.py"}],
            "warnings": [],
            "errors": [],
            "recommended_next_steps": [],
        }
        commands: list[tuple[str, ...]] = []

        def run(arguments: list[str]) -> subprocess.CompletedProcess[str]:
            commands.append(tuple(arguments))
            return completed()

        with (
            patch("scripts.workflow_check.resolve_task", return_value=TASK),
            patch("scripts.workflow_check.verify_changes", return_value=verification),
        ):
            result = check_workflow(
                "demo",
                [],
                command_runner=run,
            )
        self.assertEqual(result["status"], verification["status"])
        self.assertTrue(result["ready_to_commit"])
        self.assertFalse(result["validation_commands_executed"])
        self.assertEqual(result["validation_commands"], TASK["context"]["validation"])
        self.assertEqual(
            commands,
            [
                ("git", "diff", "--check"),
                ("git", "diff", "--cached", "--check"),
            ],
        )

    def test_scope_error_remains_error_without_cleanup(self) -> None:
        verification = {
            "status": "ERROR",
            "branch": "codex/demo",
            "risk_level": "high",
            "confirmation_required": True,
            "worktree_recommended": True,
            "actual_changes": [{"path": "shared/policy.md"}],
            "warnings": [],
            "errors": ["out of scope"],
            "recommended_next_steps": ["preserve work"],
        }
        with (
            patch("scripts.workflow_check.resolve_task", return_value=TASK),
            patch("scripts.workflow_check.verify_changes", return_value=verification),
        ):
            result = check_workflow(
                "demo",
                [],
                command_runner=lambda _args: completed(),
            )
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["write_actions_performed"], [])
        self.assertEqual(result["next_steps"], ["preserve work"])

    def test_diff_check_failure_is_error(self) -> None:
        verification = {
            "status": "PASS",
            "branch": "codex/demo",
            "risk_level": "normal",
            "confirmation_required": False,
            "worktree_recommended": False,
            "actual_changes": [{"path": "scripts/demo.py"}],
            "warnings": [],
            "errors": [],
            "recommended_next_steps": [],
        }
        with (
            patch("scripts.workflow_check.resolve_task", return_value=TASK),
            patch("scripts.workflow_check.verify_changes", return_value=verification),
        ):
            result = check_workflow(
                "demo",
                [],
                command_runner=lambda _args: completed(1, "trailing whitespace"),
            )
        self.assertEqual(result["status"], "ERROR")
        self.assertFalse(result["ready_to_commit"])

    def test_empty_worktree_passes_but_is_not_ready_to_commit(self) -> None:
        verification = {
            "status": "PASS",
            "branch": "codex/demo",
            "risk_level": "normal",
            "confirmation_required": False,
            "worktree_recommended": False,
            "actual_changes": [],
            "warnings": [],
            "errors": [],
            "recommended_next_steps": [],
        }
        with (
            patch("scripts.workflow_check.resolve_task", return_value=TASK),
            patch("scripts.workflow_check.verify_changes", return_value=verification),
        ):
            result = check_workflow(
                "demo",
                [],
                command_runner=lambda _args: completed(),
            )
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["ready_to_commit"])

    def test_forwards_agent_and_skill_authority_to_verifier(self) -> None:
        verification = {
            "status": "PASS",
            "branch": "codex/demo",
            "risk_level": "normal",
            "confirmation_required": False,
            "worktree_recommended": False,
            "actual_changes": [],
            "warnings": [],
            "errors": [],
            "recommended_next_steps": [],
        }
        with (
            patch("scripts.workflow_check.resolve_task", return_value=TASK),
            patch(
                "scripts.workflow_check.verify_changes",
                return_value=verification,
            ) as verify,
        ):
            result = check_workflow(
                "demo",
                [],
                agent_id="hermes",
                acting_skill="style-doctor",
                command_runner=lambda _args: completed(),
            )
        self.assertEqual(result["agent_id"], "hermes")
        self.assertEqual(result["acting_skill"], "style-doctor")
        self.assertEqual(verify.call_args.kwargs["agent_id"], "hermes")
        self.assertEqual(
            verify.call_args.kwargs["acting_skill"], "style-doctor"
        )


if __name__ == "__main__":
    unittest.main()
