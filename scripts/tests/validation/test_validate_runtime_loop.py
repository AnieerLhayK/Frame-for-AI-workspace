from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from scripts.validation.validate_runtime_loop import Finding, LOOP, audit, main


class RuntimeLoopValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for name in ("diagnoses", "handoffs", "patches", "validations", "generalization_backlog", "ledgers"):
            (self.root / LOOP / name).mkdir(parents=True, exist_ok=True)
        self.write_ledgers([], [], [])

    def tearDown(self) -> None:
        self.temp.cleanup()

    def packet(self, directory: str, packet_id: str, data: dict, suffix: str = "") -> None:
        path = self.root / LOOP / directory / f"{packet_id}{suffix}.md"
        path.write_text(f"# Record\n\n```yaml\n{yaml.safe_dump(data, sort_keys=False)}```\n", encoding="utf-8")

    def write_ledgers(self, diagnoses: list[list[str]], patches: list[list[str]], generalizations: list[list[str]]) -> None:
        ledgers = self.root / LOOP / "ledgers"
        self.table(ledgers / "diagnosis_ledger.md", ["diagnosis_id", "status", "linked_handoff"], diagnoses)
        self.table(ledgers / "patch_ledger.md", ["patch_id", "decision", "validation_status"], patches)
        self.table(ledgers / "generalization_ledger.md", ["generalization_id", "decision", "status"], generalizations)

    @staticmethod
    def table(path: Path, headers: list[str], rows: list[list[str]]) -> None:
        lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
        lines.extend("| " + " | ".join(row) + " |" for row in rows)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def complete_chain(self) -> None:
        self.packet("diagnoses", "DIAG-20260830-001", {"diagnosis_id": "DIAG-20260830-001"})
        self.packet("handoffs", "HANDOFF-20260830-001", {"handoff_id": "HANDOFF-20260830-001", "diagnosis_id": "DIAG-20260830-001"})
        self.packet("patches", "PATCH-20260830-001", {"patch_id": "PATCH-20260830-001", "linked_diagnosis_id": "DIAG-20260830-001", "decision": "accepted", "patch_status": "validated"})
        self.packet("validations", "VAL-20260830-001", {"validation_id": "VAL-20260830-001", "linked_patch_id": "PATCH-20260830-001", "pass_or_fail": "pass"})
        self.packet("generalization_backlog", "GEN-20260830-001", {"generalization_id": "GEN-20260830-001", "linked_patch_id": "PATCH-20260830-001", "decision": {"accepted": True}, "status": "validated"})
        self.write_ledgers(
            [["DIAG-20260830-001", "validated", "HANDOFF-20260830-001"]],
            [["PATCH-20260830-001", "accepted", "validated"]],
            [["GEN-20260830-001", "accepted", "validated"]],
        )

    def test_complete_chain_passes(self) -> None:
        self.complete_chain()
        findings, parsed = audit(self.root)
        self.assertEqual(parsed, 5)
        self.assertEqual(findings, [])

    def test_malformed_yaml_is_error(self) -> None:
        path = self.root / LOOP / "diagnoses" / "DIAG-20260830-001.md"
        path.write_text("```yaml\ndiagnosis_id: [\n```\n", encoding="utf-8")
        findings, _ = audit(self.root)
        self.assertTrue(any("malformed YAML" in item.message for item in findings))

    def test_duplicate_id_and_broken_link_are_errors(self) -> None:
        self.packet("diagnoses", "DIAG-20260830-001", {"diagnosis_id": "DIAG-20260830-001"})
        self.packet("diagnoses", "DIAG-20260830-001", {"diagnosis_id": "DIAG-20260830-001"}, "-copy")
        self.packet("handoffs", "HANDOFF-20260830-001", {"handoff_id": "HANDOFF-20260830-001", "diagnosis_id": "DIAG-20260830-999"})
        findings, _ = audit(self.root)
        text = "\n".join(item.message for item in findings)
        self.assertIn("duplicate packet id", text)
        self.assertIn("references missing", text)

    def test_unledgered_history_is_warning(self) -> None:
        self.packet("diagnoses", "DIAG-20260830-001", {"diagnosis_id": "DIAG-20260830-001"})
        findings, _ = audit(self.root)
        self.assertTrue(any(item.severity == "WARNING" and "not in its ledger" in item.message for item in findings))

    def test_strict_warning_only_exits_two(self) -> None:
        with patch(
            "scripts.validation.validate_runtime_loop.audit",
            return_value=([Finding("WARNING", "unledgered")], 1),
        ):
            self.assertEqual(main(["--strict"]), 2)

    def test_validation_diagnosis_must_match_patch(self) -> None:
        self.complete_chain()
        self.packet("diagnoses", "DIAG-20260830-002", {"diagnosis_id": "DIAG-20260830-002"})
        self.packet("validations", "VAL-20260830-001", {"validation_id": "VAL-20260830-001", "linked_patch_id": "PATCH-20260830-001", "linked_diagnosis": "DIAG-20260830-002", "pass_or_fail": "pass"})
        findings, _ = audit(self.root)
        self.assertTrue(any("diagnosis link conflicts" in item.message for item in findings))

    def test_invalid_ledger_state_is_error(self) -> None:
        self.complete_chain()
        self.write_ledgers(
            [["DIAG-20260830-001", "impossible", "HANDOFF-20260830-001"]],
            [["PATCH-20260830-001", "accepted", "validated"]],
            [["GEN-20260830-001", "accepted", "validated"]],
        )
        findings, _ = audit(self.root)
        self.assertTrue(any("invalid status" in item.message for item in findings))

    def test_packet_and_ledger_state_mismatch_is_error(self) -> None:
        self.complete_chain()
        self.write_ledgers(
            [["DIAG-20260830-001", "validated", "HANDOFF-20260830-001"]],
            [["PATCH-20260830-001", "accepted", "applied"]],
            [["GEN-20260830-001", "accepted", "validated"]],
        )
        findings, _ = audit(self.root)
        self.assertTrue(any("packet state validated conflicts with ledger applied" in item.message for item in findings))


if __name__ == "__main__":
    unittest.main()
