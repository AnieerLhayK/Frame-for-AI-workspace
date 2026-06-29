from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.report_status import ReportSpec, assess_report, parse_header


class ReportStatusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "reports").mkdir()
        (self.root / "source.txt").write_text("source", encoding="utf-8")
        self.spec = ReportSpec(
            report_id="demo",
            paths=("reports/demo.md",),
            sources=("source.txt",),
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write_report(self, commit: str = "abc123") -> Path:
        path = self.root / "reports" / "demo.md"
        path.write_text(
            "\n".join(
                [
                    "---",
                    "report_name: demo",
                    "generated_at: 2026-06-12 12:00:00 +0800",
                    f"source_commit: {commit}",
                    "report_is_snapshot: true",
                    "---",
                    "",
                    "# Demo",
                ]
            ),
            encoding="utf-8",
        )
        return path

    def test_parse_header_reads_scalar_fields(self) -> None:
        header = parse_header(self.write_report())
        self.assertEqual(header["report_name"], "demo")
        self.assertEqual(header["source_commit"], "abc123")

    def test_missing_report_is_reported(self) -> None:
        result = assess_report(self.spec, self.root, "abc123")
        self.assertEqual(result.status, "MISSING")

    def test_matching_commit_and_older_source_is_fresh(self) -> None:
        report = self.write_report()
        source = self.root / "source.txt"
        os.utime(source, (report.stat().st_mtime - 5, report.stat().st_mtime - 5))
        result = assess_report(self.spec, self.root, "abc123")
        self.assertEqual(result.status, "FRESH")

    def test_commit_change_alone_is_not_stale(self) -> None:
        self.write_report()
        result = assess_report(self.spec, self.root, "def456")
        self.assertEqual(result.status, "FRESH")

    def test_newer_source_is_stale(self) -> None:
        report = self.write_report()
        source = self.root / "source.txt"
        os.utime(source, (report.stat().st_mtime + 5, report.stat().st_mtime + 5))
        result = assess_report(self.spec, self.root, "abc123")
        self.assertEqual(result.status, "STALE")
        self.assertTrue(any("source is newer" in reason for reason in result.reasons))

    def test_missing_source_commit_header_is_stale(self) -> None:
        path = self.root / "reports" / "demo.md"
        path.write_text(
            "\n".join(
                [
                    "---",
                    "report_name: demo",
                    "generated_at: 2026-06-12 12:00:00 +0800",
                    "report_is_snapshot: true",
                    "---",
                    "",
                    "# Demo",
                ]
            ),
            encoding="utf-8",
        )
        result = assess_report(self.spec, self.root, "abc123")
        self.assertEqual(result.status, "STALE")
        self.assertIn("source_commit", result.reasons[0])

    @unittest.skipUnless(shutil.which("git"), "git is required for working-tree report checks")
    def test_regenerated_uncommitted_report_is_not_stale_by_old_report_commit(self) -> None:
        def git(*args: str) -> str:
            result = subprocess.run(
                ["git", *args],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()

        git("init")
        git("config", "user.email", "test@example.com")
        git("config", "user.name", "Test User")
        self.write_report("initial")
        git("add", ".")
        git("commit", "-m", "initial report")
        (self.root / "source.txt").write_text("updated source", encoding="utf-8")
        git("add", "source.txt")
        git("commit", "-m", "update source")
        current = git("rev-parse", "--short", "HEAD")
        self.write_report(current)

        result = assess_report(self.spec, self.root, current)

        self.assertEqual(result.status, "FRESH", result.reasons)

    @unittest.skipUnless(shutil.which("git"), "git is required for committed report checks")
    def test_committed_report_can_keep_generation_baseline_commit(self) -> None:
        def git(*args: str) -> str:
            result = subprocess.run(
                ["git", *args],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()

        git("init")
        git("config", "user.email", "test@example.com")
        git("config", "user.name", "Test User")
        self.write_report("initial")
        git("add", ".")
        git("commit", "-m", "initial report")
        baseline = git("rev-parse", "--short", "HEAD")

        (self.root / "source.txt").write_text("updated source", encoding="utf-8")
        self.write_report(baseline)
        git("add", ".")
        git("commit", "-m", "update source and report")
        current = git("rev-parse", "--short", "HEAD")

        result = assess_report(self.spec, self.root, current)

        self.assertEqual(result.status, "FRESH", result.reasons)


if __name__ == "__main__":
    unittest.main()
