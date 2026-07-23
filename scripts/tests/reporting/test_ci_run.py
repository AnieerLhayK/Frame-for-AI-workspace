from __future__ import annotations

import unittest
import tempfile

from scripts.reporting.ci_run import (
    TestSuite,
    build_test_suites,
    classify_failures,
    has_collection_error,
    summarize_results,
)
from pathlib import Path
import subprocess


class CiRunnerTests(unittest.TestCase):
    def test_collection_errors_are_blocking(self) -> None:
        output = "ERROR collecting scripts/tests/workspace/test_example.py"
        self.assertTrue(has_collection_error(output))

    def test_known_infra_failure_stays_in_infra_bucket(self) -> None:
        core, infra = classify_failures(
            "FAILED scripts/tests/workspace/test_workspace_health.py"
        )
        self.assertEqual(core, set())
        self.assertEqual(infra, {"scripts/tests/workspace/test_workspace_health.py"})

    def test_standalone_suites_use_their_own_import_roots(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scripts" / "tests").mkdir(parents=True)
            (root / "packages" / "character-system" / "engineering" / "corpus-preparation" / "qq-raw-material-filter" / "tests").mkdir(parents=True)
            (root / "skills" / "disk-scan-reporter" / "tests").mkdir(parents=True)
            suites = build_test_suites(root)
        self.assertEqual(
            [suite.name for suite in suites],
            ["workspace", "qq-raw-material-filter", "disk-scan-reporter"],
        )
        self.assertEqual(suites[0].test_path.as_posix(), "scripts/tests")
        self.assertEqual(suites[1].cwd.name, "qq-raw-material-filter")
        self.assertEqual(suites[1].test_path.as_posix(), "tests")
        self.assertEqual(suites[2].cwd.name, "disk-scan-reporter")
        self.assertEqual(suites[2].test_path.as_posix(), "tests")

    def test_missing_optional_package_suites_are_not_scheduled(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            suites = build_test_suites(root)
        self.assertEqual(
            [(suite.name, suite.cwd, suite.test_path) for suite in suites],
            [("workspace", root, Path("scripts/tests"))],
        )

    def test_summary_marks_only_infrastructure_failures_as_pass(self) -> None:
        suite = TestSuite("workspace", Path("."), Path("scripts/tests"))
        payload = summarize_results(
            [
                (
                    suite,
                    subprocess.CompletedProcess(
                        [],
                        1,
                        stdout="FAILED scripts/tests/workspace/test_workspace_health.py",
                        stderr="",
                    ),
                )
            ]
        )
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["core_failures"], [])
        self.assertEqual(len(payload["infra_failures"]), 1)

    def test_summary_marks_collection_errors_as_core_failures(self) -> None:
        suite = TestSuite("workspace", Path("."), Path("scripts/tests"))
        payload = summarize_results(
            [
                (
                    suite,
                    subprocess.CompletedProcess(
                        [], 2, stdout="ERROR collecting test_example.py", stderr=""
                    ),
                )
            ]
        )
        self.assertEqual(payload["status"], "FAIL")
        self.assertIn("workspace: <pytest collection>", payload["core_failures"])


if __name__ == "__main__":
    unittest.main()
