from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.validation.validate_project_context import validate
from scripts.workspace.project_context import load_knowledge_registry, load_task_registry


WORKSPACE_ROOT = Path(__file__).resolve().parents[3]


class ProjectContextValidationTests(unittest.TestCase):
    def test_real_project_context_layout_passes(self) -> None:
        self.assertEqual(validate(), [])

    def test_split_task_and_knowledge_loaders_preserve_entries(self) -> None:
        tasks = load_task_registry()
        knowledge = load_knowledge_registry()
        self.assertIn("public_projection_synchronization", tasks["tasks"])
        self.assertEqual(len(knowledge["topics"]), 23)
        self.assertIn("cleanup_migration", tasks["tasks"])
        self.assertIn("workspace_engineering", knowledge["topics"])

    def test_split_loaders_accept_a_small_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tasks" / "registry" / "domains").mkdir(parents=True)
            (root / "knowledge" / "topics").mkdir(parents=True)
            (root / "tasks" / "registry" / "index.yaml").write_text(
                yaml.safe_dump(
                    {
                        "schema_version": "0.2",
                        "default_rules": {},
                        "task_files": {"demo": "domains/core.yaml"},
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            (root / "tasks" / "registry" / "domains" / "core.yaml").write_text(
                yaml.safe_dump({"tasks": {"demo": {"use_when": ["test"]}}}, sort_keys=False),
                encoding="utf-8",
            )
            (root / "knowledge" / "index.yaml").write_text(
                yaml.safe_dump(
                    {
                        "schema_version": "0.2",
                        "topic_files": {"demo": "topics/demo.yaml"},
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            (root / "knowledge" / "topics" / "demo.yaml").write_text(
                yaml.safe_dump({"topics": {"demo": {"entries": []}}}, sort_keys=False),
                encoding="utf-8",
            )
            self.assertIn("demo", load_task_registry(root)["tasks"])
            self.assertIn("demo", load_knowledge_registry(root)["topics"])

    def test_retired_root_projection_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "task_registry.yaml").write_text("schema_version: '0.2'\n", encoding="utf-8")
            messages = [finding.message for finding in validate(root)]
        self.assertIn("retired compatibility projection remains: task_registry.yaml", messages)


if __name__ == "__main__":
    unittest.main()
