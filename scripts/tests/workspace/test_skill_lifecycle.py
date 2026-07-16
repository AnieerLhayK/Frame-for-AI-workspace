from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.skill_lifecycle import (
    expose_skill,
    init_skill,
    list_skills,
    projection_state,
    validate_skill,
)


class SkillLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.skill_source = self.root / "skills" / "demo"
        self.link_path = self.root / "platform" / "demo"
        self.manifest = {
            "workspace": {"source_of_truth": str(self.root)},
            "skills": [
                {
                    "id": "demo",
                    "role": "production",
                    "source_path": "skills/demo",
                    "required_files": ["SKILL.md", "README.md"],
                    "exposures": [
                        {
                            "platform": "codex",
                            "projection_id": "codex.demo",
                        }
                    ],
                }
            ],
            "projections": [
                {
                    "id": "codex.demo",
                    "platform": "codex",
                    "link_path": str(self.link_path),
                    "target_path": "skills/demo",
                }
            ],
        }

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def create_valid_skill(self) -> None:
        self.skill_source.mkdir(parents=True)
        (self.skill_source / "SKILL.md").write_text(
            "---\nname: demo\ndescription: Demo skill.\n---\n\n# demo\n",
            encoding="utf-8",
        )
        (self.skill_source / "README.md").write_text("# demo\n", encoding="utf-8")

    def test_init_creates_bounded_source_scaffold(self) -> None:
        manifest = {
            "workspace": {"source_of_truth": str(self.root)},
            "skills": [],
            "projections": [],
        }
        result = init_skill(
            manifest,
            "new-skill",
            "skills/new-skill",
            "A new test skill.",
        )

        self.assertEqual(result["status"], "CREATED")
        source = self.root / "skills" / "new-skill"
        self.assertTrue((source / "SKILL.md").is_file())
        self.assertTrue((source / "references" / "README.md").is_file())
        self.assertIn("name: new-skill", (source / "SKILL.md").read_text(encoding="utf-8"))

    def test_init_refuses_path_outside_workspace(self) -> None:
        manifest = {
            "workspace": {"source_of_truth": str(self.root)},
            "skills": [],
            "projections": [],
        }
        result = init_skill(
            manifest,
            "new-skill",
            "../outside",
            "A new test skill.",
        )
        self.assertEqual(result["status"], "BLOCKED")

    def test_validate_registered_skill(self) -> None:
        self.create_valid_skill()
        result = validate_skill(self.manifest, "demo")
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["registered"])

    def test_validate_registered_skill_without_unrequired_readme(self) -> None:
        self.skill_source.mkdir(parents=True)
        (self.skill_source / "SKILL.md").write_text(
            "---\nname: demo\ndescription: Demo skill.\n---\n\n# demo\n",
            encoding="utf-8",
        )
        self.manifest["skills"][0]["required_files"] = ["SKILL.md"]
        result = validate_skill(self.manifest, "demo")
        self.assertEqual(result["status"], "PASS")

    def test_validate_accepts_registered_source_path(self) -> None:
        self.create_valid_skill()
        result = validate_skill(self.manifest, "skills/demo")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["skill_id"], "demo")

    def test_validate_reports_frontmatter_name_mismatch(self) -> None:
        self.create_valid_skill()
        (self.skill_source / "SKILL.md").write_text(
            "---\nname: wrong\ndescription: Demo skill.\n---\n",
            encoding="utf-8",
        )
        result = validate_skill(self.manifest, "demo")
        self.assertEqual(result["status"], "ERROR")
        self.assertIn("frontmatter name", result["findings"][0])

    def test_list_reports_source_and_projection_state(self) -> None:
        self.create_valid_skill()
        result = list_skills(self.manifest)
        self.assertEqual(result["skills"][0]["source_state"], "OK")
        self.assertEqual(result["skills"][0]["projections"][0]["state"], "MISSING")

    def test_projection_state_detects_broken_or_incorrect_link(self) -> None:
        self.create_valid_skill()
        with (
            patch("scripts.skill_lifecycle.os.path.lexists", return_value=True),
            patch(
                "scripts.skill_lifecycle.os.path.realpath",
                return_value=str(self.root / "old-target"),
            ),
        ):
            state = projection_state(self.link_path, self.skill_source)
        self.assertEqual(state, "BLOCKED_EXISTING_ITEM")

    def test_expose_defaults_to_plan_without_writing(self) -> None:
        self.create_valid_skill()
        result = expose_skill(self.manifest, "demo", "codex")
        self.assertEqual(result["status"], "PLAN")
        self.assertFalse(self.link_path.exists())

    def test_expose_apply_uses_selected_projection_creator(self) -> None:
        self.create_valid_skill()
        calls: list[tuple[Path, Path]] = []

        def creator(link: Path, target: Path) -> None:
            calls.append((link, target))

        result = expose_skill(
            self.manifest,
            "demo",
            "codex",
            apply=True,
            creator=creator,
        )
        self.assertEqual(result["status"], "CREATED")
        self.assertEqual(calls, [(self.link_path.resolve(), self.skill_source.resolve())])

    def test_expose_preserves_existing_real_directory(self) -> None:
        self.create_valid_skill()
        self.link_path.mkdir(parents=True)
        result = expose_skill(
            self.manifest,
            "demo",
            "codex",
            apply=True,
        )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(self.link_path.is_dir())


if __name__ == "__main__":
    unittest.main()
