from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.session_continuity import run_audit


class SessionContinuityTests(unittest.TestCase):
    def test_audit_passes_with_live_sessions_and_backups(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            new_skill = workspace / "packages" / "demo"
            new_skill.mkdir(parents=True)

            claude_root = root / "claude"
            claude_bucket = claude_root / "projects" / "workspace"
            claude_bucket.mkdir(parents=True)
            (claude_bucket / "session.jsonl").write_text(
                json.dumps({"cwd": str(workspace)}) + "\n",
                encoding="utf-8",
            )
            claude_backup = root / "claude-backup"
            backup_bucket = claude_backup / "workspace"
            backup_bucket.mkdir(parents=True)
            (backup_bucket / "session.jsonl").write_text("{}\n", encoding="utf-8")
            (claude_backup / "SHA256.json").write_text("[]", encoding="utf-8")
            (claude_backup / "migration-map.json").write_text("{}", encoding="utf-8")

            opencode_root = root / "opencode"
            opencode_root.mkdir()
            database = opencode_root / "opencode.db"
            connection = sqlite3.connect(database)
            connection.execute("create table project (id text primary key, worktree text)")
            connection.execute(
                "create table session (id text primary key, project_id text, directory text)"
            )
            connection.execute("insert into project values (?, ?)", ("project", str(workspace)))
            connection.execute(
                "insert into session values (?, ?, ?)",
                ("session", "project", str(workspace / "old" / "demo")),
            )
            connection.commit()
            connection.close()

            opencode_backup = root / "opencode-backup"
            exports = opencode_backup / "exports"
            exports.mkdir(parents=True)
            (opencode_backup / "opencode.db").write_bytes(database.read_bytes())
            (opencode_backup / "SHA256.json").write_text("[]", encoding="utf-8")
            (opencode_backup / "migration-map.json").write_text("{}", encoding="utf-8")
            (exports / "session.json").write_text("{}", encoding="utf-8")

            manifest = {
                "session_stores": {
                    "claude": {
                        "data_root": str(claude_root),
                        "projects_path": "projects",
                    },
                    "opencode": {
                        "data_root": str(opencode_root),
                        "database_path": "opencode.db",
                    },
                }
            }
            registry = {
                "migrations": [
                    {
                        "id": "demo",
                        "workspace_root": str(workspace),
                        "path_mappings": [{"old": "old/demo", "new": "packages/demo"}],
                        "claude": {
                            "project_bucket": "workspace",
                            "backup_path": str(claude_backup),
                            "expected_transcript_files": 1,
                        },
                        "opencode": {
                            "project_id": "project",
                            "project_worktree": str(workspace),
                            "backup_path": str(opencode_backup),
                            "affected_session_ids": ["session"],
                        },
                    }
                ]
            }
            manifest_path = root / "manifest.json"
            registry_path = root / "registry.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            registry_path.write_text(json.dumps(registry), encoding="utf-8")

            payload = run_audit(manifest_path, registry_path, workspace_root=workspace)

        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["migrations"][0]["opencode"]["live_sessions"], 1)

    def test_unknown_migration_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = root / "manifest.json"
            registry = root / "registry.json"
            manifest.write_text(json.dumps({"session_stores": {}}), encoding="utf-8")
            registry.write_text(json.dumps({"migrations": []}), encoding="utf-8")
            payload = run_audit(
                manifest,
                registry,
                migration_id="missing",
                workspace_root=root,
            )
        self.assertEqual(payload["status"], "ERROR")
