from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts.plan_change_surface import (
    assess_option,
    automatic_options,
    build_plan,
    classify_path,
    is_absolute_path,
    path_in_scope,
)


SKILL_ROOTS = ("packages/character-system/engineering/generation/character-generator", "packages/character-system/runtime/characters/zyc")


class ChangeSurfacePlannerTests(unittest.TestCase):
    def test_classifies_source_and_non_source_layers(self) -> None:
        self.assertEqual(
            classify_path("packages/character-system/runtime/characters/zyc/SKILL.md", SKILL_ROOTS),
            "skill_source",
        )
        self.assertEqual(classify_path("reports/health.md", SKILL_ROOTS), "generated_report")
        self.assertEqual(classify_path("scripts/check.py", SKILL_ROOTS), "tooling")

    def test_directory_scope_allows_descendants(self) -> None:
        self.assertTrue(path_in_scope("scripts/tests/test_cli.py", ["scripts/"]))
        self.assertFalse(path_in_scope("shared/policy.md", ["scripts/"]))

    def test_external_path_is_blocked(self) -> None:
        option = assess_option(
            "projection",
            [r"C:\Users\example\.config\tool\skills\demo"],
            "behavior",
            [r"C:\Users\example\.config\tool\skills\demo"],
            SKILL_ROOTS,
        )
        self.assertEqual(option.status, "BLOCKED")

    def test_absolute_path_detection_is_cross_platform(self) -> None:
        self.assertTrue(is_absolute_path(r"C:\Users\example\skill"))
        self.assertTrue(is_absolute_path(r"\\server\share\skill"))
        self.assertTrue(is_absolute_path("/opt/tool/skill"))
        self.assertFalse(is_absolute_path("scripts/tool.py"))

    def test_generated_report_cannot_replace_tool_source(self) -> None:
        option = assess_option(
            "snapshot-only",
            ["reports/workspace_health_report.md"],
            "tooling",
            ["reports/"],
            SKILL_ROOTS,
        )
        self.assertEqual(option.status, "BLOCKED")

    def test_automatic_options_skip_declarative_scopes(self) -> None:
        options, declarative = automatic_options(
            ["scripts/", "README.md", "explicitly approved paths only"],
            SKILL_ROOTS,
        )
        self.assertIn(("tooling", ["scripts/"]), options)
        self.assertEqual(declarative, ["explicitly approved paths only"])

    def test_build_plan_prefers_tooling_over_documentation(self) -> None:
        resolved = {
            "task": {"id": "demo"},
            "context": {
                "write_scope": [
                    "scripts/tool.py",
                    "scripts/tests/test_tool.py",
                    "README.md",
                ]
            },
        }
        with (
            patch("scripts.plan_change_surface.resolve_task", return_value=resolved),
            patch("scripts.plan_change_surface.load_skill_roots", return_value=SKILL_ROOTS),
        ):
            plan = build_plan("demo", "tooling", None, [], [])
        self.assertEqual(plan["status"], "PASS")
        self.assertEqual(plan["recommendation"], "tooling")

    def test_explicit_options_compare_complete_sets(self) -> None:
        resolved = {
            "task": {"id": "demo"},
            "context": {
                "write_scope": [
                    "scripts/tool.py",
                    "scripts/tests/test_tool.py",
                    "README.md",
                ]
            },
        }
        with (
            patch("scripts.plan_change_surface.resolve_task", return_value=resolved),
            patch("scripts.plan_change_surface.load_skill_roots", return_value=SKILL_ROOTS),
        ):
            plan = build_plan(
                "demo",
                "tooling",
                "add a command",
                [],
                [
                    "implementation=scripts/tool.py,scripts/tests/test_tool.py",
                    "docs-only=README.md",
                ],
            )
        self.assertEqual(plan["recommendation"], "implementation")
        self.assertEqual(plan["options"][1]["status"], "SUPPORTING_ONLY")


if __name__ == "__main__":
    unittest.main()
