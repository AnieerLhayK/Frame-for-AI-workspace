from __future__ import annotations
import unittest
from unittest.mock import patch
from scripts.merge_safety import assess, governed_assess

class MergeSafetyTests(unittest.TestCase):
    def test_disjoint_changes_are_safe(self) -> None:
        with patch("scripts.merge_safety.git", side_effect=["base", "M\ta.py", "A\tb.py"]):
            self.assertEqual(assess("", "left", "right")["status"], "SAFE_TO_CONTINUE")
    def test_structured_overlap_stops(self) -> None:
        with patch("scripts.merge_safety.git", side_effect=["base", "M\tconfig.yaml", "M\tconfig.yaml"]):
            result = assess("", "left", "right")
        self.assertEqual(result["status"], "STOP")
        self.assertEqual(result["findings"][0]["category"], "structured_object")

    def test_governed_ff_only_requires_review_evidence(self) -> None:
        policy = {"git_branch_governance": {"integration_branch": "main", "allowed_one_shot_strategies": ["ff-only", "merge-commit"], "managed_branches": ["codex", "claude"]}}
        base = {"status": "SAFE_TO_CONTINUE", "findings": []}
        with (
            patch("scripts.merge_safety.load_yaml", return_value=policy),
            patch("scripts.merge_safety.load_registry", return_value={"agents": {"codex": {"git_branch": "codex"}}}),
            patch("scripts.merge_safety.assess", return_value=base),
            patch("scripts.merge_safety.git", return_value=""),
            patch("scripts.merge_safety.git_returncode", return_value=0),
            patch("scripts.merge_safety.merge_review_note", return_value={"status": "completed"}),
        ):
            result = governed_assess("codex", "main", agent="codex", record_id="TASK-demo", strategy="ff-only")
        self.assertEqual(result["status"], "SAFE_TO_CONTINUE")
        self.assertEqual(result["review"]["status"], "completed")

    def test_governed_agent_integration_requires_task_record(self) -> None:
        policy = {"git_branch_governance": {"integration_branch": "main", "allowed_one_shot_strategies": ["ff-only"], "managed_branches": ["codex", "claude"]}}
        with (
            patch("scripts.merge_safety.load_yaml", return_value=policy),
            patch("scripts.merge_safety.load_registry", return_value={"agents": {"codex": {"git_branch": "codex"}}}),
            patch("scripts.merge_safety.assess", return_value={"status": "SAFE_TO_CONTINUE", "findings": []}),
            patch("scripts.merge_safety.git", return_value=""),
            patch("scripts.merge_safety.git_returncode", return_value=0),
        ):
            result = governed_assess("codex", "main", agent="codex", record_id=None, strategy="ff-only")
        self.assertEqual(result["status"], "STOP")
        self.assertIn("--record-id is required for an agent-governed integration", result["errors"])
if __name__ == "__main__": unittest.main()
