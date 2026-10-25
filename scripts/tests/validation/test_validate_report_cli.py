from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


class ReportValidatorCliTests(unittest.TestCase):
    # Frame ships the manifest validator; the private protocol case subclasses
    # this contract in its own projection-excluded module.
    validators = ("manifest",)

    def test_help_check_and_legacy_write_contracts(self) -> None:
        for name in self.validators:
            with self.subTest(validator=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                report = root / "reports/current" / (
                    "manifest_validation_report.md" if name == "manifest" else "protocol_validation_report.md"
                )
                report.parent.mkdir(parents=True)
                report.write_bytes(b"existing snapshot\n")
                before = (report.read_bytes(), report.stat().st_mtime_ns)
                env = {**os.environ, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1"}

                def run(*arguments: str):
                    return subprocess.run(
                        [sys.executable, "-B", "-m", f"scripts.validation.validate_{name}", *arguments],
                        cwd=root, env=env, capture_output=True, timeout=30,
                    )

                help_result = run("--help")
                self.assertEqual(help_result.returncode, 0, help_result.stderr)
                self.assertIn(b"--check", help_result.stdout)
                self.assertEqual((report.read_bytes(), report.stat().st_mtime_ns), before)
                # Missing manifest is a real validation error, even in non-writing mode.
                checked = run("--check")
                self.assertEqual(checked.returncode, 1, checked.stderr)
                self.assertEqual((report.read_bytes(), report.stat().st_mtime_ns), before)
                unknown = run("--unknown")
                self.assertEqual(unknown.returncode, 2)
                self.assertEqual((report.read_bytes(), report.stat().st_mtime_ns), before)
                written = run()
                self.assertEqual(written.returncode, 1, written.stderr)
                self.assertNotEqual(report.read_bytes(), before[0])
                report.unlink()
                self.assertEqual(run("--check").returncode, 1)
                self.assertFalse(report.exists())
