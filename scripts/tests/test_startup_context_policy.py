from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from scripts.resolve_task_context import TokenCounter, resolve_task


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


class StartupContextPolicyTests(unittest.TestCase):
    def test_root_agents_stays_compact(self) -> None:
        counter = TokenCounter("missing-test-encoding")
        text = (WORKSPACE_ROOT / "AGENTS.md").read_text(encoding="utf-8-sig")
        registry = yaml.safe_load(
            (WORKSPACE_ROOT / "PROJECT_CONTEXT" / "task_registry.yaml").read_text(
                encoding="utf-8-sig"
            )
        )
        limit = registry["default_rules"]["context_budget"]["token_meter"][
            "root_agents_warn_tokens"
        ]
        self.assertLessEqual(
            counter.count(text),
            limit,
            "Root AGENTS.md exceeded the startup budget; route task-specific detail instead.",
        )

    def test_narrow_tasks_stay_under_warning_budget(self) -> None:
        cases = [
            ("platform_exposure", {}),
            (
                "skill_metadata_update",
                {"target-skill": ["packages/character-system/engineering/generation/character-generator"]},
            ),
        ]
        for task_id, bindings in cases:
            with self.subTest(task_id=task_id):
                result = resolve_task(
                    WORKSPACE_ROOT,
                    task_id,
                    bindings,
                    include_optional=False,
                    include_template=False,
                    count_tokens=True,
                    encoding_override="missing-test-encoding",
                )
                self.assertEqual(result["token_budget"]["status"], "PASS")

    def test_preloaded_agents_is_not_counted_twice(self) -> None:
        result = resolve_task(
            WORKSPACE_ROOT,
            "startup_context_optimization",
            {},
            include_optional=False,
            include_template=False,
            count_tokens=True,
            encoding_override="missing-test-encoding",
        )
        occurrences = [
            item
            for item in result["token_budget"]["largest_files"]
            if item["path"] == "AGENTS.md"
        ]
        self.assertEqual(len(occurrences), 1)

    def test_tasks_do_not_require_entire_shared_tree(self) -> None:
        registry = yaml.safe_load(
            (WORKSPACE_ROOT / "PROJECT_CONTEXT" / "task_registry.yaml").read_text(
                encoding="utf-8-sig"
            )
        )
        offenders = [
            task_id
            for task_id, task in registry["tasks"].items()
            if "shared/" in task.get("required", [])
        ]
        self.assertEqual(
            offenders,
            [],
            "Tasks must name specific shared protocols instead of loading shared/ wholesale.",
        )

    def test_registered_tasks_use_known_tool_profiles(self) -> None:
        registry = yaml.safe_load(
            (WORKSPACE_ROOT / "PROJECT_CONTEXT" / "task_registry.yaml").read_text(
                encoding="utf-8-sig"
            )
        )
        tool_policy = registry["default_rules"]["tool_policy"]
        profiles = tool_policy["profiles"]
        self.assertIn(tool_policy["default_profile"], profiles)
        unknown = {
            task_id: task.get("tool_profile")
            for task_id, task in registry["tasks"].items()
            if task.get("tool_profile", tool_policy["default_profile"]) not in profiles
        }
        self.assertEqual(unknown, {})

    def test_tool_profile_capability_sets_do_not_overlap(self) -> None:
        registry = yaml.safe_load(
            (WORKSPACE_ROOT / "PROJECT_CONTEXT" / "task_registry.yaml").read_text(
                encoding="utf-8-sig"
            )
        )
        profiles = registry["default_rules"]["tool_policy"]["profiles"]
        for profile_name, profile in profiles.items():
            with self.subTest(profile=profile_name):
                allow = set(profile.get("allow", []))
                confirm = set(profile.get("confirm", []))
                deny = set(profile.get("deny", []))
                self.assertFalse(allow & confirm)
                self.assertFalse(allow & deny)
                self.assertFalse(confirm & deny)


if __name__ == "__main__":
    unittest.main()
