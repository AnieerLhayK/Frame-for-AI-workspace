#!/usr/bin/env python3
"""Simulate manifest portability changes without moving files or links."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any


WORKSPACE_ROOT = Path.cwd()
MANIFEST_PATH = WORKSPACE_ROOT / "workspace_manifest.yaml"
REPORT_PATH = WORKSPACE_ROOT / "reports" / "migration_dry_run_report.md"


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8-sig"))


def get_source_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=WORKSPACE_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def replace_drive(value: str, new_drive: str) -> str:
    if len(value) >= 2 and value[1] == ":":
        return new_drive.rstrip("\\/") + value[2:]
    return value


def sync_legacy_skill_exposure_fields(manifest: dict[str, Any]) -> None:
    projections = {
        str(item.get("id", "")): item
        for item in manifest.get("projections", [])
        if isinstance(item, dict)
    }
    for skill in manifest.get("skills", []):
        exposures = skill.get("exposures", [])
        if not isinstance(exposures, list) or not exposures:
            continue
        primary = exposures[0]
        projection = projections.get(str(primary.get("projection_id", "")), {})
        skill["platform"] = str(primary.get("platform", ""))
        if projection:
            skill["projection_path"] = str(projection.get("link_path", ""))


def simulate(manifest: dict[str, Any], scenario: str, args: argparse.Namespace) -> tuple[dict[str, Any], list[str]]:
    simulated = deepcopy(manifest)
    notes: list[str] = []

    if scenario == "root-rename":
        if not args.new_root:
            raise ValueError("--new-root is required for root-rename")
        simulated["workspace"]["source_of_truth"] = args.new_root
        notes.append("workspace.source_of_truth changes; workspace-relative source paths remain stable.")
    elif scenario == "drive-change":
        if not args.new_drive:
            raise ValueError("--new-drive is required for drive-change")
        new_drive = args.new_drive.rstrip("\\/")
        simulated["workspace"]["source_of_truth"] = replace_drive(str(simulated["workspace"]["source_of_truth"]), new_drive)
        for key, value in simulated.get("platform_roots", {}).items():
            simulated["platform_roots"][key] = replace_drive(str(value), new_drive)
        for skill in simulated.get("skills", []):
            if "projection_path" in skill:
                skill["projection_path"] = replace_drive(str(skill["projection_path"]), new_drive)
        for projection in simulated.get("projections", []):
            if "link_path" in projection:
                projection["link_path"] = replace_drive(str(projection["link_path"]), new_drive)
        for key, value in simulated.get("shared", {}).get("projection_paths", {}).items():
            simulated["shared"]["projection_paths"][key] = replace_drive(str(value), new_drive)
        notes.append("Drive-letter absolute paths are rewritten in the simulated manifest only.")
    elif scenario == "shared-move":
        if not args.new_shared:
            raise ValueError("--new-shared is required for shared-move")
        new_shared = args.new_shared.replace("\\", "/")
        simulated["shared"]["source_path"] = new_shared
        for projection in simulated.get("projections", []):
            if projection.get("target_path") == "shared":
                projection["target_path"] = new_shared
        notes.append("shared.source_path and shared projection targets change; protocol paths need review if shared file layout changes.")
    elif scenario == "codex-root-change":
        if not args.new_root:
            raise ValueError("--new-root is required for codex-root-change")
        simulated["platform_roots"]["codex"] = args.new_root
        for projection in simulated.get("projections", []):
            if projection.get("platform") == "codex":
                projection["link_path"] = str(Path(args.new_root) / str(projection.get("id", "")).split(".")[-1])
        if "projection_paths" in simulated.get("shared", {}):
            simulated["shared"]["projection_paths"]["codex"] = str(Path(args.new_root) / "shared")
        notes.append("Codex platform projection root changes; source paths remain workspace-relative.")
    elif scenario == "opencode-root-change":
        if not args.new_root:
            raise ValueError("--new-root is required for opencode-root-change")
        simulated["platform_roots"]["opencode"] = args.new_root
        for projection in simulated.get("projections", []):
            if projection.get("platform") == "opencode":
                projection["link_path"] = str(Path(args.new_root) / str(projection.get("id", "")).split(".")[-1])
        if "projection_paths" in simulated.get("shared", {}):
            simulated["shared"]["projection_paths"]["opencode"] = str(Path(args.new_root) / "shared")
        notes.append("OpenCode platform projection root changes; source paths remain workspace-relative.")
    else:
        raise ValueError(f"unsupported scenario: {scenario}")

    sync_legacy_skill_exposure_fields(simulated)
    return simulated, notes


def diff_fields(original: Any, simulated: Any, prefix: str = "") -> list[dict[str, str]]:
    changes: list[dict[str, str]] = []
    if isinstance(original, dict) and isinstance(simulated, dict):
        for key in sorted(set(original) | set(simulated)):
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            changes.extend(diff_fields(original.get(key), simulated.get(key), child_prefix))
    elif isinstance(original, list) and isinstance(simulated, list):
        for index, (left, right) in enumerate(zip(original, simulated)):
            changes.extend(diff_fields(left, right, f"{prefix}[{index}]"))
        if len(original) != len(simulated):
            changes.append({"field": prefix, "current": f"list length {len(original)}", "simulated": f"list length {len(simulated)}"})
    elif original != simulated:
        changes.append({"field": prefix, "current": str(original), "simulated": str(simulated)})
    return changes


def table(rows: list[dict[str, Any]], headers: list[str]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return lines


def write_report(scenario: str, changes: list[dict[str, str]], notes: list[str]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    affected_projections = [row for row in changes if row["field"].startswith("projections") or "projection" in row["field"] or "platform_roots" in row["field"]]
    affected_reports = [
        "reports/workspace_setup_report.md",
        "reports/workspace_health_report.md",
        "reports/manifest_validation_report.md",
        "reports/migration_dry_run_report.md",
        "reports/manifest_portability_report.md",
    ]
    affected_scripts = [
        "scripts/bootstrap_workspace.py",
        "scripts/validate_manifest.py",
        "scripts/migration_dry_run.py",
        "scripts/setup_links.ps1",
        "scripts/check_links.ps1",
        "scripts/sync_report.ps1",
    ]
    affected_skill_docs = [
        "core skill SHARED_PROTOCOLS.md files only if shared policy paths change",
        "skill source files are not moved by this dry run",
    ]

    lines = [
        "---",
        "report_name: migration_dry_run_report",
        f"generated_at: {now}",
        "generated_by: scripts/migration_dry_run.py",
        f"source_root: {WORKSPACE_ROOT}",
        f"manifest_path: {MANIFEST_PATH}",
        f"source_commit: {get_source_commit()}",
        "report_scope: migration dry-run simulation",
        "report_is_snapshot: true",
        "truth_source:",
        "  - workspace_manifest.yaml",
        "  - shared/",
        "  - current git commit",
        "---",
        "",
        "Report is a snapshot. No files, directories, or links were moved.",
        "",
        "# Migration Dry Run Report",
        "",
        "## Scenario",
        "",
        f"- Scenario: `{scenario}`",
        "",
        "## Affected Manifest Fields",
        "",
        *table(changes, ["field", "current", "simulated"]),
        "",
        "## Affected Projections",
        "",
        *table(affected_projections, ["field", "current", "simulated"]),
        "",
        "## Affected Scripts",
        "",
        *[f"- {item}" for item in affected_scripts],
        "",
        "## Affected Reports",
        "",
        *[f"- {item}" for item in affected_reports],
        "",
        "## Affected Skill Docs",
        "",
        *[f"- {item}" for item in affected_skill_docs],
        "",
        "## Required Manual Steps",
        "",
        "- Review the simulated manifest changes.",
        "- Move workspace or platform directories manually outside this dry run if desired.",
        "- Update `workspace_manifest.yaml` intentionally after the real move.",
        "- Run bootstrap, manifest validation, protocol validation, sync report, and link check.",
        "- Recreate platform junctions only after explicit approval.",
        "",
        "## Safe To Automate?",
        "",
        "- Manifest analysis: yes.",
        "- File moves: no.",
        "- Junction relinking: no.",
        "",
        "## Risks",
        "",
        "- Absolute platform roots are local deployment data and may not exist on the target machine.",
        "- Reports may contain stale absolute paths until regenerated.",
        "- Existing platform tools may cache old projection paths.",
        "",
        "## Rollback Advice",
        "",
        "- Keep the current Git commit as the source checkpoint.",
        "- Do not delete old platform projections until new link checks pass.",
        "- Revert manifest path edits if validation or link checks fail.",
        "",
        "## Notes",
        "",
        *[f"- {note}" for note in notes],
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run manifest migration simulations without moving files.")
    parser.add_argument("--scenario", required=True, choices=["root-rename", "drive-change", "shared-move", "codex-root-change", "opencode-root-change"])
    parser.add_argument("--new-root", help="New root path for root or platform-root scenarios.")
    parser.add_argument("--new-drive", help="New drive prefix, for example E:.")
    parser.add_argument("--new-shared", help="New workspace-relative shared path.")
    args = parser.parse_args()

    if not MANIFEST_PATH.is_file():
        print("[ERROR] workspace_manifest.yaml missing")
        return 1

    try:
        manifest = load_manifest()
        simulated, notes = simulate(manifest, args.scenario, args)
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 1

    changes = diff_fields(manifest, simulated)
    write_report(args.scenario, changes, notes)
    print(f"Migration dry-run report: {REPORT_PATH.relative_to(WORKSPACE_ROOT).as_posix()}")
    print(f"Scenario: {args.scenario}")
    print(f"Affected manifest fields: {len(changes)}")
    print("No files, directories, or links were moved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
