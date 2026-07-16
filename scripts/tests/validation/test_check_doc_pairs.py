from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.check_doc_pairs import (
    analyze_changes,
    companion_for,
    primary_for,
    validate_existing_coverage,
)


class DocPairCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.registry = {
            "directories": [
                {
                    "path": "docs",
                    "pattern": "*.md",
                    "recursive": True,
                    "companion_suffix": ".zh-CN.md",
                }
            ],
            "pairs": [
                {
                    "primary": "PROJECT_CONTEXT/README.md",
                    "companion": "PROJECT_CONTEXT/README.zh-CN.md",
                }
            ],
        }

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_companion_path_helpers(self) -> None:
        self.assertEqual(companion_for("docs/guide.md"), "docs/guide.zh-CN.md")
        self.assertEqual(primary_for("docs/guide.zh-CN.md"), "docs/guide.md")

    def test_changed_primary_warns_when_existing_companion_is_unchanged(self) -> None:
        companion = self.root / "docs" / "guide.zh-CN.md"
        companion.parent.mkdir(parents=True)
        companion.write_text("中文", encoding="utf-8")

        payload = analyze_changes(self.root, self.registry, [(" M", "docs/guide.md")])

        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(len(payload["warnings"]), 1)
        self.assertIn("docs/guide.md -> docs/guide.zh-CN.md", payload["warnings"][0])

    def test_strict_mode_errors_on_unsynced_companion(self) -> None:
        companion = self.root / "PROJECT_CONTEXT" / "README.zh-CN.md"
        companion.parent.mkdir(parents=True)
        companion.write_text("中文", encoding="utf-8")

        payload = analyze_changes(
            self.root,
            self.registry,
            [(" M", "PROJECT_CONTEXT/README.md")],
            strict=True,
        )

        self.assertEqual(payload["status"], "ERROR")
        self.assertEqual(len(payload["errors"]), 1)

    def test_new_zh_companion_under_registered_directory_passes(self) -> None:
        payload = analyze_changes(self.root, self.registry, [("??", "docs/new.zh-CN.md")])

        self.assertEqual(payload["status"], "PASS")
        self.assertFalse(payload["errors"])

    def test_new_zh_companion_outside_registered_directory_errors(self) -> None:
        payload = analyze_changes(self.root, self.registry, [("??", "other/new.zh-CN.md")])

        self.assertEqual(payload["status"], "ERROR")
        self.assertIn("unregistered zh-CN companion", payload["errors"][0])

    def test_exact_registered_companion_passes(self) -> None:
        payload = analyze_changes(
            self.root,
            self.registry,
            [(" M", "PROJECT_CONTEXT/README.zh-CN.md")],
        )

        self.assertEqual(payload["status"], "PASS")
        self.assertFalse(payload["errors"])

    def test_existing_coverage_accepts_directory_rules(self) -> None:
        primary = self.root / "docs" / "guide.md"
        companion = self.root / "docs" / "guide.zh-CN.md"
        companion.parent.mkdir(parents=True)
        primary.write_text("English", encoding="utf-8")
        companion.write_text("中文", encoding="utf-8")

        self.assertEqual(validate_existing_coverage(self.root, self.registry), [])

    def test_existing_coverage_reports_unregistered_companion(self) -> None:
        primary = self.root / "other" / "guide.md"
        companion = self.root / "other" / "guide.zh-CN.md"
        companion.parent.mkdir(parents=True)
        primary.write_text("English", encoding="utf-8")
        companion.write_text("中文", encoding="utf-8")

        errors = validate_existing_coverage(self.root, self.registry)

        self.assertEqual(len(errors), 1)
        self.assertIn("not registered", errors[0])


if __name__ == "__main__":
    unittest.main()
