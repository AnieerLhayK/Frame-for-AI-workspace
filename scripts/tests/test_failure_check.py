from __future__ import annotations

import unittest

from scripts.failure_check import diagnose_payload


class FailureCheckTests(unittest.TestCase):
    def test_ready_when_no_active_resource_findings(self) -> None:
        result = diagnose_payload(
            {
                "task": {"id": "demo"},
                "context": {"resource_findings": [], "unresolved_placeholders": []},
                "errors": [],
                "warnings": [],
            },
            include_optional=False,
        )
        self.assertEqual(result["status"], "READY")
        self.assertTrue(result["can_continue"])
        self.assertTrue(any("--include-optional" in action for action in result["actions"]))

    def test_required_missing_is_blocked(self) -> None:
        result = diagnose_payload(
            {
                "task": {"id": "demo"},
                "context": {
                    "unresolved_placeholders": [],
                    "resource_findings": [
                        {
                            "severity": "ERROR",
                            "resource_class": "required",
                            "reason": "missing",
                            "resource": "src/required.md",
                            "expected": "D:/workspace/src/required.md",
                        }
                    ],
                },
                "errors": ["Missing required resource"],
                "warnings": [],
            },
            include_optional=False,
        )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(result["can_continue"])

    def test_optional_missing_is_degraded(self) -> None:
        result = diagnose_payload(
            {
                "task": {"id": "demo"},
                "context": {
                    "unresolved_placeholders": [],
                    "resource_findings": [
                        {
                            "severity": "WARNING",
                            "resource_class": "optional",
                            "reason": "missing",
                            "resource": "reports/optional.md",
                            "expected": "D:/workspace/reports/optional.md",
                            "impact": "continuing in degraded mode",
                        }
                    ],
                },
                "errors": [],
                "warnings": ["Missing optional resource"],
            },
            include_optional=True,
        )
        self.assertEqual(result["status"], "DEGRADED")
        self.assertTrue(result["can_continue"])

    def test_unresolved_placeholder_produces_binding_action(self) -> None:
        result = diagnose_payload(
            {
                "task": {"id": "demo"},
                "context": {
                    "resource_findings": [],
                    "unresolved_placeholders": ["target-skill"],
                },
                "errors": ["Unresolved required placeholder"],
                "warnings": [],
            },
            include_optional=False,
        )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(
            any(
                "--bind target-skill=<workspace-relative-value>" in action
                for action in result["actions"]
            )
        )

    def test_path_escape_never_suggests_searching_elsewhere(self) -> None:
        result = diagnose_payload(
            {
                "task": {"id": "demo"},
                "context": {
                    "unresolved_placeholders": [],
                    "resource_findings": [
                        {
                            "severity": "ERROR",
                            "resource_class": "required",
                            "reason": "path_escape",
                            "resource": "../outside.md",
                            "expected": "a workspace-contained path",
                        }
                    ],
                },
                "errors": ["Required resource path blocked"],
                "warnings": [],
            },
            include_optional=False,
        )
        self.assertTrue(
            any("do not search outside" in action for action in result["actions"])
        )


if __name__ == "__main__":
    unittest.main()
