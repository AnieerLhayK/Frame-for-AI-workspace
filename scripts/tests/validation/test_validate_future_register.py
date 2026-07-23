from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.validate_future_register import validate


class FutureRegisterValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "history").mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_registry(self, relative: str, payload: dict) -> None:
        (self.root / relative).write_text(
            yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
        )

    def write_valid_documents(
        self,
        *,
        option_status: str = "candidate",
        history_option_status: str = "implemented",
        duplicate_id: bool = False,
        archive_metadata: dict | None = None,
    ) -> None:
        self.write_registry(
            "optimization_options.yaml",
            {
                "schema_version": "0.2",
                "options": [
                    {"id": "OPT-active", "title": "Active option", "status": option_status}
                ],
            },
        )
        self.write_registry(
            "risk_register.yaml",
            {
                "schema_version": "0.2",
                "risks": [
                    {"id": "RISK-active", "title": "Active risk", "status": "observed"}
                ],
            },
        )
        metadata = {
            "archived_at": "2026-07-18",
            "source_registry": "PROJECT_CONTEXT/potential_for_future/optimization_options.yaml",
        }
        if archive_metadata:
            metadata.update(archive_metadata)
        self.write_registry(
            "history/optimization_options.yaml",
            {
                "schema_version": "0.2",
                "options": [
                    {
                        "id": "OPT-active" if duplicate_id else "OPT-history",
                        "title": "Historical option",
                        "status": history_option_status,
                        **metadata,
                    }
                ],
            },
        )
        self.write_registry(
            "history/risk_register.yaml",
            {
                "schema_version": "0.2",
                "risks": [
                    {
                        "id": "RISK-history",
                        "title": "Historical risk",
                        "status": "mitigated",
                        "archived_at": "2026-07-18",
                        "source_registry": "PROJECT_CONTEXT/potential_for_future/risk_register.yaml",
                    }
                ],
            },
        )

    def test_valid_active_and_history_documents_pass(self) -> None:
        self.write_valid_documents()
        self.assertEqual(validate(self.root), [])

    def test_empty_registries_pass(self) -> None:
        for relative, key in (
            ("optimization_options.yaml", "options"),
            ("risk_register.yaml", "risks"),
            ("history/optimization_options.yaml", "options"),
            ("history/risk_register.yaml", "risks"),
        ):
            self.write_registry(relative, {"schema_version": "0.2", key: []})
        self.assertEqual(validate(self.root), [])

    def test_terminal_status_in_active_registry_fails(self) -> None:
        self.write_valid_documents(option_status="implemented")
        messages = [finding.message for finding in validate(self.root)]
        self.assertTrue(any("disallowed status" in message for message in messages))

    def test_nonterminal_status_in_history_fails(self) -> None:
        self.write_valid_documents(history_option_status="candidate")
        messages = [finding.message for finding in validate(self.root)]
        self.assertTrue(any("disallowed status" in message for message in messages))

    def test_duplicate_ids_across_active_and_history_fail(self) -> None:
        self.write_valid_documents(duplicate_id=True)
        messages = [finding.message for finding in validate(self.root)]
        self.assertTrue(any("duplicates id OPT-active" in message for message in messages))

    def test_missing_or_invalid_migration_metadata_fails(self) -> None:
        self.write_valid_documents(
            archive_metadata={
                "archived_at": "not-a-date",
                "source_registry": "wrong.yaml",
            }
        )
        messages = [finding.message for finding in validate(self.root)]
        self.assertTrue(any("archived_at is not" in message for message in messages))
        self.assertTrue(any("source_registry must be" in message for message in messages))

    def test_missing_migration_metadata_fails(self) -> None:
        self.write_valid_documents()
        history_path = self.root / "history" / "optimization_options.yaml"
        history = yaml.safe_load(history_path.read_text(encoding="utf-8"))
        del history["options"][0]["archived_at"]
        history_path.write_text(yaml.safe_dump(history, sort_keys=False), encoding="utf-8")
        messages = [finding.message for finding in validate(self.root)]
        self.assertTrue(any("requires archived_at" in message for message in messages))

    def test_yaml_parse_error_fails(self) -> None:
        self.write_valid_documents()
        (self.root / "risk_register.yaml").write_text("risks: [", encoding="utf-8")
        messages = [finding.message for finding in validate(self.root)]
        self.assertTrue(any("cannot parse YAML" in message for message in messages))


if __name__ == "__main__":
    unittest.main()
