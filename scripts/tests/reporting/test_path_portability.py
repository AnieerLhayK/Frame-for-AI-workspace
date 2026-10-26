from __future__ import annotations
import unittest
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch
from scripts.reporting.path_portability import classify_reference, collect_findings


class PathPortabilityTests(unittest.TestCase):
    def test_history_and_fixtures_are_visible_but_not_runtime_defaults(self):
        for name in ["PROJECT_CONTEXT/tasks/records/2026/10/26/TASK.json", "packages/example/reports/evidence.md", "scripts/tests/workspace/test_example.py"]:
            category, reason, review = classify_reference(name, "ROOT=/old/workspace", "/old/workspace", set())
            self.assertFalse(review, name)
            self.assertTrue(reason)

    def test_active_source_and_current_memory_still_need_review(self):
        for name in ["scripts/workspace/runtime.py", "PROJECT_CONTEXT/continuity/current_status.md"]:
            self.assertTrue(classify_reference(name, "ROOT=/old/workspace", "/old/workspace", set())[2])

    def test_catalog_only_explains_projection_fields(self):
        name = "skills/content/registry.json"
        self.assertFalse(classify_reference(name, '{"projection_path":"/old/workspace/skill"}', "/old/workspace", {name})[2])
        self.assertTrue(classify_reference(name, '{"source_path":"/old/workspace/skill"}', "/old/workspace", {name})[2])

    def test_signature_file_does_not_exempt_new_runtime_defaults(self):
        name = "scripts/publishing/publish_policy.py"
        self.assertFalse(classify_reference(name, '(re.escape("/old/workspace"), "replacement"),', "/old/workspace", set())[2])
        self.assertTrue(classify_reference(name, 'ROOT = "/old/workspace"', "/old/workspace", set())[2])

    def test_windows_and_posix_file_names_classify_identically(self):
        path = "PROJECT_CONTEXT/tasks/ledger/2026/10/26.md"
        self.assertEqual(classify_reference(path, "x", "x", set()), classify_reference(path.replace("/", chr(92)), "x", "x", set()))

    def test_collector_preserves_unknown_active_reference_and_stops_without_git(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            file = root / "active.py"
            file.write_text(str(root), encoding="utf8")
            manifest = {"workspace": {"source_of_truth": str(root)}}
            completed = subprocess.CompletedProcess([], 0, b"active.py\0", b"")
            with patch("scripts.reporting.path_portability.subprocess.run", return_value=completed):
                rows = collect_findings(root, manifest)
            self.assertTrue(rows)
            self.assertTrue(all(row["RequiresReview"] for row in rows))
            with patch("scripts.reporting.path_portability.subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")):
                with self.assertRaises(subprocess.CalledProcessError):
                    collect_findings(root, manifest)

    def test_executable_sources_in_report_or_history_directories_still_require_review(self):
        for path in ["scripts/reports/loader.py", "reports/current/loader.py", "packages/example/reports/runner.ps1", "WORKSPACE_ENGINEERING/evidence/runner.js", "reports/README.md"]:
            self.assertTrue(classify_reference(path, "ROOT=/old/workspace", "/old/workspace", set())[2], path)
