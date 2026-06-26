from __future__ import annotations

import os
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

    def test_commit_change_is_stale(self) -> None:
        self.write_report()
        result = assess_report(self.spec, self.root, "def456")
        self.assertEqual(result.status, "STALE")
        self.assertIn("source commit changed", result.reasons[0])

    def test_newer_source_is_stale(self) -> None:
        report = self.write_report()
        source = self.root / "source.txt"
        os.utime(source, (report.stat().st_mtime + 5, report.stat().st_mtime + 5))
        result = assess_report(self.spec, self.root, "abc123")
        self.assertEqual(result.status, "STALE")
        self.assertTrue(any("source is newer" in reason for reason in result.reasons))


if __name__ == "__main__":
    unittest.main()
