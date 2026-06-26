from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.find_knowledge import (
    find_topics,
    list_topics,
    load_registry,
    topic_score,
    validate_registry,
)


class KnowledgeFinderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = {
            "topics": {
                "skill_design": {
                    "title": "Reusable skill design",
                    "aliases": ["skill development", "skill 开发", "搭建经验"],
                    "entries": [
                        {
                            "path": "WORKSPACE_ENGINEERING/skill_engineering/skill_design_patterns.md",
                            "layer": "workspace_engineering",
                            "purpose": "Reusable patterns.",
                        }
                    ],
                },
                "current_status": {
                    "title": "Current project state",
                    "aliases": ["status", "工程现状"],
                    "entries": [
                        {
                            "path": "PROJECT_CONTEXT/current_status.md",
                            "layer": "project_context",
                            "purpose": "Current state.",
                        }
                    ],
                },
                "project_boundaries": {
                    "title": "Project and repository boundaries",
                    "aliases": ["项目边界", "Claude 串仓"],
                    "entries": [
                        {
                            "path": "ARCHITECTURE.md",
                            "layer": "documentation",
                            "purpose": "Repository boundaries.",
                        }
                    ],
                },
                "runtime_drift": {
                    "title": "Runtime drift repair",
                    "aliases": ["运行时漂移", "诊断修复"],
                    "entries": [
                        {
                            "path": "packages/character-system/shared/runtime_loop_policy.md",
                            "layer": "shared",
                            "purpose": "Runtime repair policy.",
                        }
                    ],
                },
            }
        }

    def test_exact_alias_scores_above_token_overlap(self) -> None:
        score, reasons = topic_score(
            "skill_design",
            self.registry["topics"]["skill_design"],
            "搭建经验",
        )
        self.assertEqual(score, 100)
        self.assertIn("exact alias", reasons)

    def test_chinese_alias_finds_current_status(self) -> None:
        result = find_topics(self.registry, "工程现状", 3, None)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["matches"][0]["topic_id"], "current_status")

    def test_chinese_project_boundary_alias_finds_boundary_topic(self) -> None:
        result = find_topics(self.registry, "Claude 串仓", 3, None)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["matches"][0]["topic_id"], "project_boundaries")

    def test_runtime_drift_alias_finds_runtime_topic(self) -> None:
        result = find_topics(self.registry, "运行时漂移", 3, None)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["matches"][0]["topic_id"], "runtime_drift")

    def test_exact_alias_suppresses_low_score_noise(self) -> None:
        result = find_topics(self.registry, "skill development", 3, None)
        self.assertEqual([match["topic_id"] for match in result["matches"]], ["skill_design"])

    def test_layer_filter_removes_other_layers(self) -> None:
        result = find_topics(self.registry, "skill development", 3, "project_context")
        self.assertEqual(result["status"], "NO_MATCH")

    def test_legacy_skill_engineering_layer_alias_routes_to_workspace_engineering(self) -> None:
        result = find_topics(self.registry, "skill development", 3, "skill_engineering")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["matches"][0]["entries"][0]["layer"],
            "workspace_engineering",
        )

    def test_list_topics_does_not_read_entry_files(self) -> None:
        result = list_topics(self.registry)
        self.assertEqual(len(result["topics"]), 4)
        self.assertNotIn("entries", result["topics"][0])

    def test_registry_requires_topics_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "registry.yaml"
            path.write_text(yaml.safe_dump({"topics": []}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_registry(path)

    def test_validate_registry_reports_missing_paths(self) -> None:
        result = validate_registry(
            {
                "topics": {
                    "missing": {
                        "entries": [
                            {
                                "path": "definitely/missing.md",
                                "layer": "project_context",
                                "purpose": "Missing.",
                            }
                        ]
                    }
                }
            }
        )
        self.assertEqual(result["status"], "ERROR")
        self.assertIn("missing indexed path", result["warnings"][0])


class RegisteredKnowledgeRoutesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_registry()

    def test_runtime_usage_routes_to_runtime_reference(self) -> None:
        result = find_topics(self.registry, "运行时 skill", 3, None)
        self.assertEqual(result["matches"][0]["topic_id"], "runtime_skill_usage")
        paths = {entry["path"] for entry in result["matches"][0]["entries"]}
        self.assertIn("USAGE_GUIDES/REFERENCE/runtime/zyc.md", paths)

    def test_character_generator_routes_to_engineering_reference(self) -> None:
        result = find_topics(self.registry, "character generator", 3, None)
        self.assertEqual(result["matches"][0]["topic_id"], "skill_engineering_operations")
        paths = {entry["path"] for entry in result["matches"][0]["entries"]}
        self.assertIn(
            "USAGE_GUIDES/REFERENCE/engineering/generation/character-generator.md",
            paths,
        )

    def test_opencode_loading_routes_to_platform_guide(self) -> None:
        result = find_topics(self.registry, "OpenCode loading", 3, None)
        self.assertEqual(result["matches"][0]["topic_id"], "platform_loading_guides")
        paths = {entry["path"] for entry in result["matches"][0]["entries"]}
        self.assertIn("USAGE_GUIDES/QUICK_START/opencode.md", paths)

    def test_workflow_query_routes_to_workflow_references(self) -> None:
        result = find_topics(self.registry, "角色生成流程", 3, None)
        self.assertEqual(result["matches"][0]["topic_id"], "skill_workflows")
        paths = {entry["path"] for entry in result["matches"][0]["entries"]}
        self.assertIn("USAGE_GUIDES/REFERENCE/workflows/generate_character.md", paths)

    def test_workspace_engineering_routes_to_reference_book(self) -> None:
        result = find_topics(self.registry, "workspace engineering", 3, None)
        self.assertEqual(result["matches"][0]["topic_id"], "workspace_engineering")
        paths = {entry["path"] for entry in result["matches"][0]["entries"]}
        self.assertIn("WORKSPACE_ENGINEERING/README.md", paths)


if __name__ == "__main__":
    unittest.main()
