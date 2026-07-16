from __future__ import annotations

import unittest

from scripts.reporting.ci_run import classify_failures, has_collection_error


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


if __name__ == "__main__":
    unittest.main()
