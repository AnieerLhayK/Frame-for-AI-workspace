from __future__ import annotations

import tempfile
import unittest
import subprocess
from pathlib import Path
from unittest.mock import patch

import yaml

from scripts.workspace import task_ledger, task_records


class TaskRecordsTests(unittest.TestCase):
    def test_concurrent_sessions_can_hold_write_registrations(self) -> None:
        from argparse import Namespace
        args = Namespace(task_type="demo", tokens_estimated=1, bind=[],
                         operation=["workspace_write"], started_at="2026-09-08T00:00:00Z",
                         owner_agent="codex", owner_session="one")
        with tempfile.TemporaryDirectory() as directory, patch.object(
            task_records, "RECORD_ROOT", Path(directory)
        ), patch.object(task_records, "capture_git_baseline", return_value=None):
            first = task_records.start(args)
            args.owner_session = "two"
            second = task_records.start(args)
            for record in (first, second):
                self.assertEqual(task_records.active_registration(
                    record["task_id"], "workspace_write")["status"], "active")
            self.assertNotEqual(first["task_id"], second["task_id"])

    def test_git_baseline_records_status_and_fingerprints_without_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def git(*args: str) -> None:
                subprocess.run(
                    ["git", *args], cwd=root, check=True, capture_output=True, text=True
                )

            git("init")
            git("config", "user.email", "test@example.com")
            git("config", "user.name", "Test")
            (root / "tracked.txt").write_text("original\n", encoding="utf-8")
            git("add", "tracked.txt")
            git("commit", "-m", "baseline")
            (root / "tracked.txt").write_text("worktree secret\n", encoding="utf-8")
            (root / "staged.txt").write_text("staged secret\n", encoding="utf-8")
            git("add", "staged.txt")
            (root / "untracked.txt").write_text("untracked secret\n", encoding="utf-8")

            with patch.object(task_records, "ROOT", root):
                baseline = task_records.capture_git_baseline(
                    captured_at="2026-08-28T00:00:00Z"
                )

        by_path = {entry["path"]: entry for entry in baseline["paths"]}
        self.assertEqual(set(by_path), {"staged.txt", "tracked.txt", "untracked.txt"})
        self.assertEqual(by_path["tracked.txt"]["worktree_status"], "M")
        self.assertEqual(by_path["staged.txt"]["index_status"], "A")
        self.assertIsNotNone(by_path["staged.txt"]["index_blob"])
        self.assertEqual(by_path["untracked.txt"]["index_status"], "?")
        self.assertIsNone(by_path["untracked.txt"]["index_blob"])
        self.assertNotIn("secret", str(baseline))

    def test_new_records_use_schema_14_and_finalize_preserves_it(self) -> None:
        baseline = {
            "branch": "codex/demo",
            "head_commit": "a" * 40,
            "captured_at": "2026-08-28T00:00:00Z",
            "paths": [],
        }
        args = type(
            "Args",
            (),
            {
                "task_type": "demo",
                "tokens_estimated": 1,
                "bind": [],
                "operation": ["workspace_write"],
                "started_at": "2026-08-28T00:00:00Z",
                "owner_agent": None,
                "owner_session": None,
            },
        )()
        with tempfile.TemporaryDirectory() as directory, patch.object(
            task_records, "RECORD_ROOT", Path(directory) / "records"
        ), patch.object(
            task_ledger, "DESTINATION", Path(directory) / "ledger"
        ), patch.object(task_records, "capture_git_baseline", return_value=baseline):
            record = task_records.start(args)
            final = task_records.finalize(
                type(
                    "FinalizeArgs",
                    (),
                    {
                        "task_id": record["task_id"],
                        "ended_at": "2026-08-28T00:01:00Z",
                        "status": "successful",
                        "validation": "passed",
                        "usability": "usable",
                        "human_edit_rounds": 0,
                        "command": [],
                        "tokens_actual": None,
                        "tokens_saved": None,
                        "currency_cost": None,
                    },
                )()
            )
        self.assertEqual(final["schema_version"], "1.4")
        self.assertEqual(final["git_baseline"], baseline)

    def test_ledger_receipt_requires_all_migrated_task_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory)
            (ledger / "2026" / "07").mkdir(parents=True)
            (ledger / "2026" / "07" / "18.md").write_text(
                "# Task Ledger\n\n### TASK-20260718-001 - demo\n", encoding="utf-8"
            )
            (ledger / "migration_receipt.yaml").write_text(
                yaml.safe_dump(
                    {
                        "schema_version": "1.0",
                        "source_commit": "demo",
                        "source_path": "old.md",
                        "source_blob": "blob",
                        "source_sha256": "hash",
                        "task_ids": ["TASK-20260718-001"],
                    }
                ),
                encoding="utf-8",
            )
            with patch.object(task_ledger, "DESTINATION", ledger), patch.object(
                task_ledger, "MIGRATION_RECEIPT", ledger / "migration_receipt.yaml"
            ), patch.object(task_ledger, "LEGACY_DIRECTORY", ledger / "legacy"), patch.object(
                task_ledger, "git_blob_matches", return_value=True
            ):
                self.assertTrue(task_ledger.validate())
                receipt = yaml.safe_load((ledger / "migration_receipt.yaml").read_text(encoding="utf-8"))
                receipt["task_ids"].append("TASK-20260718-999")
                (ledger / "migration_receipt.yaml").write_text(yaml.safe_dump(receipt), encoding="utf-8")
                self.assertFalse(task_ledger.validate())
                receipt["task_ids"].pop()
                (ledger / "migration_receipt.yaml").write_text(yaml.safe_dump(receipt), encoding="utf-8")
                (ledger / "legacy").mkdir()
                (ledger / "legacy" / "old.md").write_text("legacy", encoding="utf-8")
                self.assertFalse(task_ledger.validate())

    def test_validate_rejects_success_without_validation(self) -> None:
        record = {"schema_version": "1.0", "task_id": "TASK-20260715-001", "started_at": "2026-07-15T00:00:00Z", "status": "successful", "validation": {"status": "not_run"}, "human_edit_rounds": 0, "tokens": {"estimated": 1, "actual": None, "saved": None}, "usability": {"status": "usable"}}
        self.assertIn("successful records require validation", task_records.validate_record(record))

    def test_record_path_is_year_month_day_partitioned(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(task_records, "RECORD_ROOT", Path(directory)):
            path = task_records.record_path("TASK-20260715-001", "2026-07-15T00:00:00Z")
        self.assertEqual(path.parts[-4:], ("2026", "07", "15", "TASK-20260715-001.json"))

    def test_active_registration_requires_declared_operation(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            task_records, "RECORD_ROOT", Path(directory)
        ):
            record = task_records.initial_record(
                "TASK-20260715-001",
                task_type="demo",
                started_at="2026-07-15T00:00:00Z",
                tokens_estimated=0,
                operations=["workspace_write"],
            )
            path = task_records.record_path(record["task_id"], record["started_at"])
            task_records.create_record(path, record)
            active = task_records.active_registration(
                "TASK-20260715-001", "workspace_write"
            )
            self.assertEqual(active["status"], "active")
            with self.assertRaisesRegex(ValueError, "external_write"):
                task_records.active_registration(
                    "TASK-20260715-001", "external_write"
                )

    def test_active_registration_rejects_historical_unregistered_record(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            task_records, "RECORD_ROOT", Path(directory)
        ):
            record = {
                "schema_version": "1.0",
                "task_id": "TASK-20260715-001",
                "started_at": "2026-07-15T00:00:00Z",
                "status": "in_progress",
                "validation": {"status": "not_run"},
                "human_edit_rounds": 0,
                "tokens": {"estimated": 0, "actual": None, "saved": None},
                "usability": {"status": "unknown"},
            }
            path = task_records.record_path(record["task_id"], record["started_at"])
            task_records.create_record(path, record)
            with self.assertRaisesRegex(ValueError, "not registered"):
                task_records.active_registration(
                    "TASK-20260715-001", "workspace_write"
                )

    def test_start_measures_routed_context_when_no_estimate_is_supplied(self) -> None:
        args = type(
            "Args",
            (),
            {
                "task_type": "demo",
                "tokens_estimated": None,
                "bind": [],
                "operation": ["workspace_write"],
                "started_at": "2026-07-15T00:00:00Z",
            },
        )()
        with tempfile.TemporaryDirectory() as directory, patch.object(
            task_records, "RECORD_ROOT", Path(directory)
        ), patch.object(task_records, "resolve_tokens_estimated", return_value=321) as resolve:
            record = task_records.start(args)
        self.assertEqual(record["tokens"]["estimated"], 321)
        resolve.assert_called_once_with("demo", [])

    def test_start_persists_workspace_session_owner_and_bindings(self) -> None:
        baseline = {
            "branch": "codex/test",
            "head_commit": "a" * 40,
            "captured_at": "2026-07-15T00:00:00Z",
            "paths": [],
        }
        args = type(
            "Args",
            (),
            {
                "task_type": "runtime_drift_fix",
                "tokens_estimated": 123,
                "bind": ["target-character=packages/character-system/runtime/characters/zyc"],
                "operation": ["workspace_write"],
                "started_at": "2026-07-15T00:00:00Z",
                "owner_agent": "opencode",
                "owner_session": "session-1",
            },
        )()
        with tempfile.TemporaryDirectory() as directory, patch.object(
            task_records, "RECORD_ROOT", Path(directory)
        ), patch.object(
            task_records, "capture_git_baseline", return_value=baseline
        ):
            record = task_records.start(args)
        self.assertEqual(
            record["owner"],
            {
                "kind": "workspace_session",
                "agent": "opencode",
                "session_id": "session-1",
                "bindings": [
                    "target-character=packages/character-system/runtime/characters/zyc"
                ],
            },
        )
        self.assertFalse(task_records.validate_record(record))

    def test_workspace_session_owner_requires_both_identity_fields(self) -> None:
        args = type(
            "Args",
            (),
            {"owner_agent": "opencode", "owner_session": None, "bind": []},
        )()
        with self.assertRaisesRegex(ValueError, "supplied together"):
            task_records.workspace_session_owner(args)

    def test_explicit_token_estimate_skips_resolution(self) -> None:
        args = type(
            "Args",
            (),
            {"task_type": "demo", "tokens_estimated": 123, "bind": []},
        )()
        with patch.object(task_records, "resolve_tokens_estimated") as resolve:
            self.assertEqual(task_records.tokens_estimated(args), 123)
        resolve.assert_not_called()

    def test_external_start_records_registered_actor_and_client_root(self) -> None:
        baseline = {
            "branch": "codex/test",
            "head_commit": "a" * 40,
            "captured_at": "2026-07-16T00:00:00Z",
            "paths": [],
        }
        args = type(
            "Args",
            (),
            {
                "agent": "external-host",
                "client_root": "/external-host",
                "task_type": "demo",
                "tokens_estimated": 123,
                "bind": ["name=demo"],
                "operation": ["workspace_write"],
                "started_at": "2026-07-16T00:00:00Z",
            },
        )()
        with tempfile.TemporaryDirectory() as directory, patch.object(
            task_records, "RECORD_ROOT", Path(directory)
        ), patch.object(task_records, "external_agent_id", return_value="opencode"), patch.object(
            task_records, "external_client_root", return_value="/external-host"
        ), patch.object(
            task_records, "capture_git_baseline", return_value=baseline
        ):
            record = task_records.external_start(args)
        self.assertEqual(record["origin"], {
            "kind": "external_workspace",
            "agent": "opencode",
            "client_root": "/external-host",
            "bindings": ["name=demo"],
        })
        self.assertFalse(task_records.validate_record(record))

    def test_external_client_root_requires_existing_directory_outside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace_root = root / "workspace"
            client_root = root / "client"
            workspace_root.mkdir()
            client_root.mkdir()
            with patch.object(task_records, "ROOT", workspace_root):
                self.assertEqual(task_records.external_client_root(str(client_root)), str(client_root))
                with self.assertRaisesRegex(ValueError, "outside"):
                    task_records.external_client_root(str(workspace_root / "nested"))
                with self.assertRaisesRegex(ValueError, "existing directory"):
                    task_records.external_client_root(str(root / "missing"))

    def test_report_usage_updates_active_external_task_and_rejects_other_actor(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            task_records, "RECORD_ROOT", Path(directory)
        ), patch.object(task_records, "external_agent_id", side_effect=lambda value: value):
            record = task_records.initial_record(
                "TASK-20260716-001",
                task_type="demo",
                started_at="2026-07-16T00:00:00Z",
                tokens_estimated=0,
                operations=["workspace_write"],
            )
            record["origin"] = {
                "kind": "external_workspace",
                "agent": "opencode",
                "client_root": "/external-host",
            }
            path = task_records.record_path(record["task_id"], record["started_at"])
            task_records.create_record(path, record)
            args = type("Args", (), {
                "task_id": record["task_id"],
                "agent": "opencode",
                "usage_json": '{"source":"external_host","input_tokens":120,"output_tokens":30,"currency_cost":0.02}',
                "usage_file": None,
            })()
            updated = task_records.report_usage(args)
            args.agent = "other"
            with self.assertRaisesRegex(ValueError, "does not match"):
                task_records.report_usage(args)
        self.assertEqual(updated["tokens"]["actual"], 150)
        self.assertEqual(updated["tokens"]["currency_cost"], 0.02)
        self.assertEqual(updated["usage"]["transport"], "external_cli")

    def test_active_external_registration_binds_agent_and_client_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace_root = root / "workspace"
            client_root = root / "client"
            other_root = root / "other"
            workspace_root.mkdir()
            client_root.mkdir()
            other_root.mkdir()
            with patch.object(task_records, "RECORD_ROOT", root / "task_records"), patch.object(
                task_records, "ROOT", workspace_root
            ), patch.object(task_records, "external_agent_id", side_effect=lambda value: value):
                record = task_records.initial_record(
                    "TASK-20260716-001", task_type="demo", started_at="2026-07-16T00:00:00Z",
                    tokens_estimated=0, operations=["workspace_write"],
                )
                record["origin"] = {
                    "kind": "external_workspace", "agent": "opencode", "client_root": str(client_root),
                }
                task_records.create_record(
                    task_records.record_path(record["task_id"], record["started_at"]), record
                )
                self.assertEqual(
                    task_records.active_external_registration(
                        record["task_id"], agent="opencode", client_root=str(client_root)
                    )["status"],
                    "active",
                )
                with self.assertRaisesRegex(ValueError, "require --external-client-root"):
                    task_records.active_registration(record["task_id"], "workspace_write")
                with self.assertRaisesRegex(ValueError, "client root does not match"):
                    task_records.active_external_registration(
                        record["task_id"], agent="opencode", client_root=str(other_root)
                    )

    def test_finalize_preserves_usage_reported_during_external_task(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(task_records, "RECORD_ROOT", root / "task_records"), patch.object(
                task_ledger, "DESTINATION", root / "task_ledger"
            ), patch.object(task_records, "external_agent_id", side_effect=lambda value: value):
                record = task_records.initial_record(
                    "TASK-20260716-001",
                    task_type="demo",
                    started_at="2026-07-16T00:00:00Z",
                    tokens_estimated=0,
                    operations=["workspace_write"],
                )
                record["origin"] = {
                    "kind": "external_workspace",
                    "agent": "opencode",
                    "client_root": "/external-host",
                }
                path = task_records.record_path(record["task_id"], record["started_at"])
                task_records.create_record(path, record)
                task_records.report_usage(type("Args", (), {
                    "task_id": record["task_id"], "agent": "opencode",
                    "usage_json": '{"source":"external_host","total_tokens":150}',
                    "usage_file": None,
                })())
                final = task_records.finalize(type("Args", (), {
                    "task_id": record["task_id"], "ended_at": "2026-07-16T00:10:00Z",
                    "status": "successful", "validation": "passed", "usability": "usable",
                    "human_edit_rounds": 0, "command": [], "tokens_actual": None,
                    "tokens_saved": None, "currency_cost": None,
                })())
        self.assertEqual(final["tokens"]["actual"], 150)
        self.assertEqual(final["usage"]["status"], "recorded")

    def test_report_usage_file_is_limited_to_the_external_client_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            client_root = root / "client"
            client_root.mkdir()
            allowed = client_root / "usage.json"
            allowed.write_text('{"source":"external_host","total_tokens":5}', encoding="utf-8")
            outside = root / "outside.json"
            outside.write_text('{"source":"external_host","total_tokens":5}', encoding="utf-8")
            with patch.object(task_records, "RECORD_ROOT", root / "task_records"), patch.object(
                task_records, "external_agent_id", side_effect=lambda value: value
            ):
                record = task_records.initial_record(
                    "TASK-20260716-001", task_type="demo", started_at="2026-07-16T00:00:00Z",
                    tokens_estimated=0, operations=["workspace_write"],
                )
                record["origin"] = {
                    "kind": "external_workspace", "agent": "opencode", "client_root": str(client_root),
                }
                task_records.create_record(
                    task_records.record_path(record["task_id"], record["started_at"]), record
                )
                args = type("Args", (), {
                    "task_id": record["task_id"], "agent": "opencode",
                    "usage_json": None, "usage_file": str(allowed),
                })()
                self.assertEqual(task_records.report_usage(args)["tokens"]["actual"], 5)
                args.usage_file = str(outside)
                with self.assertRaisesRegex(ValueError, "inside the external client root"):
                    task_records.report_usage(args)

    def test_merge_review_skip_requires_reason_and_is_structured(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(
            task_records, "RECORD_ROOT", Path(directory)
        ):
            record = task_records.initial_record(
                "TASK-20260716-001", task_type="demo", started_at="2026-07-16T00:00:00Z",
                tokens_estimated=0, operations=["workspace_write"],
            )
            path = task_records.record_path(record["task_id"], record["started_at"])
            task_records.create_record(path, record)
            args = type("Args", (), {
                "task_id": record["task_id"], "status": "skipped_user_approved",
                "source_branch": "codex", "target_branch": "main", "strategy": "ff-only",
                "review_base": "main", "reason": "User approved a narrow documentation merge.",
            })()
            updated = task_records.add_merge_review_note(args)
        self.assertEqual(updated["notes"][0]["kind"], "merge_review")
        self.assertFalse(task_records.validate_record(updated))

    def test_finalize_collects_explicit_host_usage_without_provider_call(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(task_records, "RECORD_ROOT", root / "task_records"), patch.object(
                task_ledger, "DESTINATION", root / "task_ledger"
            ), patch.dict(
                "os.environ",
                {
                    "WORKSPACE_TASK_USAGE_JSON": (
                        '{"task_id":"TASK-20260716-001","source":"codex_host",'
                        '"input_tokens":120,"output_tokens":30,"currency_cost":0.02}'
                    )
                },
                clear=False,
            ):
                record = task_records.initial_record(
                    "TASK-20260716-001",
                    task_type="task_outcome_records",
                    started_at="2026-07-16T00:00:00Z",
                    tokens_estimated=0,
                    operations=["workspace_write"],
                )
                path = task_records.record_path(record["task_id"], record["started_at"])
                task_records.create_record(path, record)
                result = task_records.finalize(
                    type("Args", (), {
                        "task_id": record["task_id"], "ended_at": "2026-07-16T00:10:00Z",
                        "status": "successful", "validation": "passed", "usability": "usable",
                        "human_edit_rounds": 0, "command": [], "tokens_actual": None,
                        "tokens_saved": None, "currency_cost": None,
                    })()
                )
        self.assertEqual(result["tokens"]["actual"], 150)
        self.assertEqual(result["tokens"]["currency_cost"], 0.02)
        self.assertEqual(result["usage"]["status"], "recorded")

    def test_host_usage_rejects_a_mismatched_task_id(self) -> None:
        with patch.dict(
            "os.environ",
            {"WORKSPACE_TASK_USAGE_JSON": '{"task_id":"TASK-20260716-999","source":"host","total_tokens":1}'},
            clear=False,
        ):
            usage = task_records.host_usage("TASK-20260716-001")
        self.assertEqual(usage["status"], "unavailable")
        self.assertEqual(usage["reason"], "usage_task_id_mismatch")

    def test_finalize_syncs_one_idempotent_ledger_entry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record_root = root / "task_records"
            ledger_root = root / "task_ledger"
            with patch.object(task_records, "RECORD_ROOT", record_root), patch.object(
                task_ledger, "DESTINATION", ledger_root
            ):
                record = task_records.initial_record(
                    "TASK-20260716-001",
                    task_type="task_outcome_records",
                    started_at="2026-07-16T00:00:00Z",
                    tokens_estimated=0,
                    operations=["workspace_write"],
                )
                path = task_records.record_path(record["task_id"], record["started_at"])
                task_records.create_record(path, record)
                args = type(
                    "Args",
                    (),
                    {
                        "task_id": record["task_id"],
                        "ended_at": "2026-07-16T00:10:00Z",
                        "status": "successful",
                        "validation": "passed",
                        "usability": "usable",
                        "human_edit_rounds": 0,
                        "command": ["python -m unittest"],
                        "tokens_actual": None,
                        "tokens_saved": None,
                        "currency_cost": None,
                    },
                )()

                task_records.finalize(args)
                task_records.sync_ledger(type("Args", (), {"task_id": None, "date": "2026-07-16"})())

            ledger = ledger_root / "2026" / "07" / "16.md"
            content = ledger.read_text(encoding="utf-8")
            self.assertEqual(content.count("### TASK-20260716-001"), 1)
            self.assertIn("automatic task-outcome record synchronization", content)


if __name__ == "__main__":
    unittest.main()
