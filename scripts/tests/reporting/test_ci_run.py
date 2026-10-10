from __future__ import annotations

import unittest
import tempfile
import json
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from scripts.reporting.ci_run import (
    TestSuite,
    build_test_suites,
    classify_failures,
    has_collection_error,
    summarize_results,
    main,
    run_test_suites,
)
from pathlib import Path
import subprocess


class CiRunnerTests(unittest.TestCase):
    def make_manifest(self, root: Path, disk_scan_source: str | None = None) -> None:
        skills = [] if disk_scan_source is None else [
            {"id": "disk-scan-reporter", "source_path": disk_scan_source}
        ]
        (root / "workspace_manifest.yaml").write_text(json.dumps({"skills": skills}), encoding="utf-8")

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
            self.make_manifest(root, "skills/governance/disk-scan-reporter")
            (root / "scripts" / "tests").mkdir(parents=True)
            (root / "packages" / "character-system" / "engineering" / "corpus-preparation" / "qq-raw-material-filter" / "tests").mkdir(parents=True)
            (root / "skills" / "governance" / "disk-scan-reporter" / "tests").mkdir(parents=True)
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
            self.make_manifest(root)
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

    def test_registered_disk_scan_tests_cannot_be_silently_omitted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_manifest(root, "skills/governance/disk-scan-reporter")
            with self.assertRaisesRegex(ValueError, "disk-scan-reporter"):
                build_test_suites(root)

    def test_disk_scan_root_follows_manifest_instead_of_a_fixed_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_manifest(root, "relocated/scan-owner")
            (root / "relocated/scan-owner/tests").mkdir(parents=True)
            suites = build_test_suites(root)
            self.assertEqual(suites[-1].cwd, (root / "relocated/scan-owner").resolve())

    def test_timeout_preserves_output_blocks_and_continues_other_suites(self) -> None:
        suites = (
            TestSuite("workspace", Path("."), Path("scripts/tests")),
            TestSuite("other", Path("other"), Path("tests")),
        )
        timed_out = subprocess.TimeoutExpired(
            ["pytest"], 7,
            output=b"FAILED scripts/tests/workspace/test_workspace_health.py\npartial",
            stderr=b"timeout details",
        )
        with patch("scripts.reporting.ci_run.build_test_suites", return_value=suites), patch(
            "scripts.reporting.ci_run.subprocess.run",
            side_effect=[timed_out, subprocess.CompletedProcess([], 0, stdout="passed", stderr="")],
        ) as run:
            results = run_test_suites(verbose=False, suite_timeout=7)
        self.assertEqual(run.call_count, 2)
        self.assertEqual(run.call_args_list[0].kwargs["timeout"], 7)
        self.assertIn("partial", results[0][1].stdout)
        self.assertIn("timeout details", results[0][1].stderr)
        payload = summarize_results(results)
        self.assertEqual(payload["status"], "FAIL")
        self.assertIn("workspace: <suite timeout after 7s>", payload["core_failures"])
        self.assertTrue(payload["suites"][0]["timed_out"])
        self.assertFalse(payload["suites"][1]["timed_out"])
        self.assertGreaterEqual(payload["suites"][0]["duration_seconds"], 0)
        self.assertIn("partial", payload["suites"][0]["stdout"])
        self.assertIn("timeout details", payload["suites"][0]["stderr"])

    def test_pytest_launch_failure_is_reported_for_the_correct_suite(self) -> None:
        suite = TestSuite("workspace", Path("."), Path("scripts/tests"))
        with patch("scripts.reporting.ci_run.build_test_suites", return_value=(suite,)), patch(
            "scripts.reporting.ci_run.subprocess.run", side_effect=OSError("cannot launch pytest"),
        ):
            payload = summarize_results(run_test_suites(verbose=False))
        self.assertEqual(payload["status"], "FAIL")
        self.assertIn("workspace: <pytest exit 1>", payload["core_failures"])
        self.assertIn("cannot launch pytest", payload["suites"][0]["stderr"])

    def test_default_timeout_is_600_seconds(self) -> None:
        suite = TestSuite("workspace", Path("."), Path("scripts/tests"))
        with patch("scripts.reporting.ci_run.build_test_suites", return_value=(suite,)), patch(
            "scripts.reporting.ci_run.subprocess.run",
            return_value=subprocess.CompletedProcess([], 0, stdout="passed", stderr=""),
        ) as run:
            run_test_suites(verbose=False)
        self.assertEqual(run.call_args.kwargs["timeout"], 600)

    def test_invalid_timeout_is_an_argument_error(self) -> None:
        for value in ("0", "-1", "1.5", "bad"):
            with self.subTest(value=value), patch("scripts.reporting.ci_run.run_test_suites") as run:
                with self.assertRaises(SystemExit) as caught:
                    main(["--suite-timeout", value])
                self.assertEqual(caught.exception.code, 2)
                run.assert_not_called()

    def test_json_discovery_error_is_blocking_without_traceback(self) -> None:
        output = StringIO()
        with patch("scripts.reporting.ci_run.build_test_suites", side_effect=ValueError("missing disk-scan-reporter tests")), redirect_stdout(output):
            self.assertEqual(main(["--format", "json"]), 1)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["status"], "FAIL")
        self.assertIn("<suite discovery>", payload["core_failures"])


if __name__ == "__main__":
    unittest.main()
