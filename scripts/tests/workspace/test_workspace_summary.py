from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.workspace_summary import (
    build_summary,
    cli_commands,
    parse_recent_ledger,
    workspace_tag_state,
)


class WorkspaceSummaryTests(unittest.TestCase):
    def test_cli_commands_are_derived_from_parser(self) -> None:
        commands = cli_commands()
        self.assertIn("task", commands)
        self.assertIn("health", commands)
        self.assertIn("launcher", commands)
        self.assertIn("summary", commands)

    def test_parse_recent_ledger_respects_limit(self) -> None:
        ledger = """# Task Ledger

### TASK-20260613-002 - Newer task

- Date: 2026-06-13
- Status: done
- Task type: newer
- Branch: main
- Commit: abc1234

### TASK-20260612-001 - Older task

- Date: 2026-06-12
- Status: done
- Task type: older
- Branch: main
- Commit: def5678
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "ledger.md"
            path.write_text(ledger, encoding="utf-8")
            entries = parse_recent_ledger(path, limit=1)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["id"], "TASK-20260613-002")
        self.assertEqual(entries[0]["commit"], "abc1234")

    def test_parse_recent_ledger_reads_newest_day_first(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "2026" / "06").mkdir(parents=True)
            (root / "2026" / "07").mkdir()
            (root / "2026" / "06" / "01.md").write_text("### TASK-20260601-001 - Old\n\n- Date: 2026-06-01\n", encoding="utf-8")
            (root / "2026" / "07" / "01.md").write_text("### TASK-20260701-001 - New\n\n- Date: 2026-07-01\n", encoding="utf-8")
            entries = parse_recent_ledger(root, limit=1)
        self.assertEqual(entries[0]["id"], "TASK-20260701-001")

    @patch("scripts.workspace_summary.git_output")
    def test_workspace_tag_state_uses_manifest_version_tag(self, git_output) -> None:
        git_output.side_effect = ["v1.1.0", "6"]

        tag, commits_ahead = workspace_tag_state("1.1.0")

        self.assertEqual(tag, "v1.1.0")
        self.assertEqual(commits_ahead, 6)
        git_output.assert_any_call(
            ["describe", "--tags", "--match", "v1.1.0", "--abbrev=0"]
        )

    @patch("scripts.workspace_summary.git_output")
    def test_workspace_tag_state_ignores_unrelated_component_tag(self, git_output) -> None:
        git_output.return_value = ""

        tag, commits_ahead = workspace_tag_state("1.1.0")

        self.assertIsNone(tag)
        self.assertIsNone(commits_ahead)

    @patch("scripts.workspace_summary.parse_recent_ledger")
    @patch("scripts.workspace_summary.cli_commands")
    @patch("scripts.workspace_summary.load_knowledge_registry")
    @patch("scripts.workspace_summary.load_task_registry")
    @patch("scripts.workspace_summary.load_yaml")
    @patch("scripts.workspace_summary.git_output")
    def test_build_summary_combines_live_sources(
        self,
        git_output,
        load_yaml,
        task_registry,
        knowledge_registry,
        cli_command_list,
        recent_entries,
    ) -> None:
        git_output.side_effect = [
            "v1.0.0",
            "4",
            "main",
            "abc1234",
            "v1.0.0-4-gabc1234",
            "",
        ]
        load_yaml.side_effect = [
            {
                "workspace": {
                    "workspace_name": "example",
                    "workspace_version": "1.0.0",
                    "source_of_truth": "D:/example",
                    "manifest_path": "workspace_manifest.yaml",
                },
                "skills": [{}, {}],
                "packages": [{}],
                "projections": [{}],
                "protocols": [{}, {}, {}],
            },
        ]
        task_registry.return_value = {"tasks": {"one": {}, "two": {}}}
        knowledge_registry.return_value = {"topics": {"overview": {}}}
        cli_command_list.return_value = ["health", "summary"]
        recent_entries.return_value = [{"id": "TASK-1", "title": "Example"}]

        summary = build_summary(recent=1)

        self.assertEqual(summary["workspace"]["name"], "example")
        self.assertEqual(summary["git"]["workspace_tag"], "v1.0.0")
        self.assertEqual(summary["git"]["commits_ahead"], 4)
        self.assertTrue(summary["git"]["clean"])
        self.assertEqual(summary["inventory"]["skills"], 2)
        self.assertEqual(summary["inventory"]["packages"], 1)
        self.assertEqual(summary["inventory"]["workspace_protocols"], 3)
        self.assertEqual(summary["inventory"]["task_routes"], 2)
        self.assertEqual(summary["inventory"]["cli_commands"], ["health", "summary"])


if __name__ == "__main__":
    unittest.main()
