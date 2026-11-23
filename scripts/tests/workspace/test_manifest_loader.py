from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.workspace.manifest_loader import load_manifest


class ManifestLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_json(self, relative: str, payload: dict) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_aggregates_category_and_active_package_skills(self) -> None:
        self.write_json("workspace_manifest.yaml", {
            "skill_catalogs": {"skills": "skills", "external-skills": "external-skills"},
            "packages": [{"id": "demo", "source_path": "packages/demo", "package_catalog": "packages/demo/package_manifest.json"}],
        })
        self.write_json("skills/catalog.json", {"categories": ["engineering/registry.json"]})
        (self.root / "skills/engineering/owned").mkdir(parents=True)
        (self.root / "skills/engineering/owned/SKILL.md").write_text("owned", encoding="utf-8")
        self.write_json("skills/engineering/registry.json", {
            "owner": "skills", "category": "engineering",
            "skills": [{"id": "owned", "source_path": "skills/engineering/owned"}],
        })
        self.write_json("external-skills/catalog.json", {"categories": []})
        self.write_json("packages/demo/package_manifest.json", {
            "package_id": "demo",
            "skills": [
                {"id": "package-skill", "source_path": "packages/demo/skills/package-skill", "status": "active", "workspace_registered": True},
                {"id": "dev-skill", "source_path": "packages/demo/skills/dev-skill", "status": "development", "workspace_registered": False},
            ],
        })
        for skill_id in ("package-skill", "dev-skill"):
            skill_root = self.root / "packages/demo/skills" / skill_id
            skill_root.mkdir(parents=True)
            (skill_root / "SKILL.md").write_text(skill_id, encoding="utf-8")

        loaded = load_manifest(self.root / "workspace_manifest.yaml")

        self.assertEqual([item["id"] for item in loaded["skills"]], ["owned", "package-skill"])

    def test_rejects_catalog_paths_that_escape_workspace(self) -> None:
        self.write_json("workspace_manifest.yaml", {
            "skill_catalogs": {"skills": "../outside", "external-skills": "external-skills"},
        })
        with self.assertRaisesRegex(ValueError, "escapes Workspace source"):
            load_manifest(self.root / "workspace_manifest.yaml")

    def test_rejects_duplicate_ids(self) -> None:
        self.write_json("workspace_manifest.yaml", {
            "skill_catalogs": {"skills": "skills", "external-skills": "external-skills"},
            "packages": [],
        })
        self.write_json("external-skills/catalog.json", {"categories": []})
        self.write_json("skills/catalog.json", {"categories": ["engineering/registry.json", "governance/registry.json"]})
        for category in ("engineering", "governance"):
            skill_root = self.root / f"skills/{category}/same"
            skill_root.mkdir(parents=True)
            (skill_root / "SKILL.md").write_text("same", encoding="utf-8")
            self.write_json(f"skills/{category}/registry.json", {
                "owner": "skills", "category": category,
                "skills": [{"id": "same", "source_path": f"skills/{category}/same"}],
            })
        with self.assertRaisesRegex(ValueError, "duplicate registered skill id"):
            load_manifest(self.root / "workspace_manifest.yaml")

    def test_legacy_manifest_is_returned_without_catalog_changes(self) -> None:
        legacy = {"skills": [{"id": "legacy"}]}
        self.write_json("workspace_manifest.yaml", legacy)
        self.assertEqual(load_manifest(self.root / "workspace_manifest.yaml"), legacy)


if __name__ == "__main__":
    unittest.main()
