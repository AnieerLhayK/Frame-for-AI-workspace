from __future__ import annotations

import unittest

from scripts.workspace_explain import (
    explain_mechanism,
    explain_path,
    explain_topic,
)


class WorkspaceExplainTests(unittest.TestCase):
    def test_explain_path_finds_layer_tasks_topics_and_tests(self) -> None:
        result = explain_path("scripts/workspace_cli.py")
        self.assertEqual(result["mode"], "path")
        self.assertTrue(result["exists"])
        self.assertEqual(result["layer"], "tooling")
        self.assertIn("scripts/tests/test_workspace_cli.py", result["test_candidates"])
        self.assertTrue(any(row["id"] == "developer_interface_tooling" for row in result["tasks"]))
        self.assertTrue(any(row["topic"] == "developer_interfaces" for row in result["knowledge_topics"]))

    def test_explain_topic_returns_registered_knowledge_entries(self) -> None:
        result = explain_topic("developer interface", 2)
        self.assertEqual(result["mode"], "topic")
        self.assertTrue(result["matches"])
        self.assertEqual(result["matches"][0]["id"], "developer_interfaces")

    def test_explain_known_mechanism(self) -> None:
        result = explain_mechanism("task-routing")
        self.assertEqual(result["mode"], "mechanism")
        self.assertEqual(result["name"], "task-routing")
        self.assertIn("workspace task resolve <task-id>", result["entrypoints"])

    def test_explain_unknown_mechanism_lists_known_values(self) -> None:
        result = explain_mechanism("missing")
        self.assertEqual(result["error"], "unknown mechanism")
        self.assertIn("task-routing", result["known_mechanisms"])


if __name__ == "__main__":
    unittest.main()
