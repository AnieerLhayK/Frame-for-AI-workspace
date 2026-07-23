from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


from scripts.workspace.project_context import PROJECT_CONTEXT_ROOT
from scripts.workspace.runtime import WORKSPACE_ROOT
MANIFEST_PATH = WORKSPACE_ROOT / "workspace_manifest.yaml"
REGISTRY_PATH = PROJECT_CONTEXT_ROOT / "continuity" / "session_migrations.json"


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected an object in {path}")
    return payload


def normalize_path(value: str) -> str:
    return value.replace("\\", "/").rstrip("/").casefold()


def resolve_external(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def audit_claude(
    store: dict[str, Any],
    migration: dict[str, Any],
) -> dict[str, Any]:
    data_root = Path(str(store.get("data_root", "")))
    project_dir = data_root / str(store.get("projects_path", "projects")) / str(
        migration.get("claude", {}).get("project_bucket", "")
    )
    transcript_files = sorted(project_dir.glob("*.jsonl")) if project_dir.is_dir() else []
    parse_errors = 0
    observed_cwds: set[str] = set()
    for transcript in transcript_files:
        for line in transcript.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                parse_errors += 1
                continue
            if isinstance(payload, dict) and isinstance(payload.get("cwd"), str):
                observed_cwds.add(payload["cwd"])

    details = migration.get("claude", {})
    backup = Path(str(details.get("backup_path", "")))
    backup_bucket = backup / str(details.get("project_bucket", ""))
    expected = int(details.get("expected_transcript_files", 0))
    backup_files = sorted(backup_bucket.glob("*.jsonl")) if backup_bucket.is_dir() else []
    passed = (
        project_dir.is_dir()
        and len(transcript_files) >= expected
        and parse_errors == 0
        and backup.is_dir()
        and len(backup_files) >= expected
        and (backup / "SHA256.json").is_file()
        and (backup / "migration-map.json").is_file()
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "project_dir": str(project_dir),
        "transcript_files": len(transcript_files),
        "parse_errors": parse_errors,
        "observed_cwds": sorted(observed_cwds),
        "backup_path": str(backup),
        "backup_transcript_files": len(backup_files),
    }


def audit_opencode(
    store: dict[str, Any],
    migration: dict[str, Any],
) -> dict[str, Any]:
    data_root = Path(str(store.get("data_root", "")))
    database = data_root / str(store.get("database_path", "opencode.db"))
    details = migration.get("opencode", {})
    expected_ids = {str(item) for item in details.get("affected_session_ids", [])}
    project_id = str(details.get("project_id", ""))
    live_ids: set[str] = set()
    historical_directories: dict[str, int] = {}
    project_worktree = ""
    error = ""

    if database.is_file():
        try:
            connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
            connection.row_factory = sqlite3.Row
            project = connection.execute(
                "select id, worktree from project where id = ?",
                (project_id,),
            ).fetchone()
            if project is not None:
                project_worktree = str(project["worktree"])
            rows = connection.execute(
                "select id, directory from session where project_id = ?",
                (project_id,),
            ).fetchall()
            live_ids = {str(row["id"]) for row in rows}
            old_paths = [
                normalize_path(str(item.get("old", "")))
                for item in migration.get("path_mappings", [])
                if isinstance(item, dict)
            ]
            workspace_root = normalize_path(str(migration.get("workspace_root", "")))
            for row in rows:
                directory = normalize_path(str(row["directory"] or ""))
                for old in old_paths:
                    full_old = f"{workspace_root}/{old}"
                    if directory == full_old or directory.startswith(f"{full_old}/"):
                        historical_directories[full_old] = (
                            historical_directories.get(full_old, 0) + 1
                        )
            connection.close()
        except sqlite3.Error as exc:
            error = str(exc)

    backup = Path(str(details.get("backup_path", "")))
    exports = backup / "exports"
    valid_exports = 0
    for session_id in expected_ids:
        export_path = exports / f"{session_id}.json"
        try:
            json.loads(export_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        valid_exports += 1

    expected_worktree = normalize_path(str(details.get("project_worktree", "")))
    passed = (
        database.is_file()
        and not error
        and normalize_path(project_worktree) == expected_worktree
        and expected_ids.issubset(live_ids)
        and backup.is_dir()
        and (backup / "opencode.db").is_file()
        and (backup / "SHA256.json").is_file()
        and (backup / "migration-map.json").is_file()
        and valid_exports == len(expected_ids)
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "database": str(database),
        "project_id": project_id,
        "project_worktree": project_worktree,
        "expected_sessions": len(expected_ids),
        "live_sessions": len(expected_ids & live_ids),
        "historical_directories": historical_directories,
        "backup_path": str(backup),
        "valid_exports": valid_exports,
        "error": error or None,
    }


def audit_migration(
    manifest: dict[str, Any],
    migration: dict[str, Any],
    workspace_root: Path = WORKSPACE_ROOT,
) -> dict[str, Any]:
    path_checks = []
    for mapping in migration.get("path_mappings", []):
        old_path = workspace_root / Path(str(mapping.get("old", "")))
        new_path = workspace_root / Path(str(mapping.get("new", "")))
        path_checks.append(
            {
                "old": str(old_path),
                "old_exists": old_path.exists(),
                "new": str(new_path),
                "new_exists": new_path.is_dir(),
            }
        )

    stores = manifest.get("session_stores", {})
    claude = audit_claude(stores.get("claude", {}), migration)
    opencode = audit_opencode(stores.get("opencode", {}), migration)
    paths_pass = all(item["new_exists"] for item in path_checks)
    status = "PASS" if paths_pass and claude["status"] == "PASS" and opencode["status"] == "PASS" else "FAIL"
    return {
        "id": migration.get("id"),
        "status": status,
        "path_checks": path_checks,
        "claude": claude,
        "opencode": opencode,
    }


def run_audit(
    manifest_path: Path = MANIFEST_PATH,
    registry_path: Path = REGISTRY_PATH,
    migration_id: str | None = None,
    workspace_root: Path = WORKSPACE_ROOT,
) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    registry = load_json(registry_path)
    migrations = [
        item
        for item in registry.get("migrations", [])
        if isinstance(item, dict) and (migration_id is None or item.get("id") == migration_id)
    ]
    if migration_id and not migrations:
        return {
            "status": "ERROR",
            "workspace_root": str(workspace_root),
            "migrations": [],
            "error": f"Unknown migration id: {migration_id}",
            "note": "Read-only audit; no session data was changed.",
        }
    results = [audit_migration(manifest, item, workspace_root) for item in migrations]
    return {
        "status": "PASS" if results and all(item["status"] == "PASS" for item in results) else "FAIL",
        "workspace_root": str(workspace_root),
        "migrations": results,
        "note": "Read-only audit; no session data was changed.",
    }


def render_text(payload: dict[str, Any]) -> None:
    print(f"Session continuity: {payload['status']}")
    for migration in payload.get("migrations", []):
        print(f"- {migration['id']}: {migration['status']}")
        claude = migration["claude"]
        opencode = migration["opencode"]
        print(
            f"  Claude: {claude['status']} - {claude['transcript_files']} live transcripts, "
            f"{claude['backup_transcript_files']} backed up."
        )
        print(
            f"  OpenCode: {opencode['status']} - {opencode['live_sessions']}/"
            f"{opencode['expected_sessions']} sessions live, {opencode['valid_exports']} exports valid."
        )
    if payload.get("error"):
        print(f"Error: {payload['error']}")
    print(payload["note"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit session continuity after workspace path migrations.")
    parser.add_argument("--migration-id")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    payload = run_audit(migration_id=args.migration_id)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        render_text(payload)
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
