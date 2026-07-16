#!/usr/bin/env python3
"""Validate the character-system protocol contract layer.

Run from the workspace root:

    python scripts/validate_protocols.py

The validator is intentionally conservative. It checks durable contract drift
without requiring every document to share identical prose.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


WORKSPACE_ROOT = Path.cwd()
WORKSPACE_MANIFEST_PATH = WORKSPACE_ROOT / "workspace_manifest.yaml"
PROTOCOL_MANIFEST_PATH = (
    WORKSPACE_ROOT
    / "packages"
    / "character-system"
    / "shared"
    / "protocol_manifest.json"
)
REPORT_PATH = WORKSPACE_ROOT / "reports" / "protocol_validation_report.md"


@dataclass
class Finding:
    severity: str
    message: str


class ValidationState:
    def __init__(self) -> None:
        self.errors: list[Finding] = []
        self.warnings: list[Finding] = []
        self.info: list[Finding] = []
        self.checked_protocols: list[dict[str, Any]] = []
        self.checked_skills: list[dict[str, Any]] = []
        self.checked_templates: list[dict[str, Any]] = []
        self.checked_ledgers: list[dict[str, Any]] = []
        self.schema_status: list[dict[str, Any]] = []

    def add(self, severity: str, message: str) -> None:
        finding = Finding(severity=severity, message=message)
        if severity == "ERROR":
            self.errors.append(finding)
        elif severity == "WARNING":
            self.warnings.append(finding)
        else:
            self.info.append(finding)


def rel_path(path: Path) -> str:
    try:
        return path.relative_to(WORKSPACE_ROOT).as_posix()
    except ValueError:
        return str(path)


def resolve_workspace_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return WORKSPACE_ROOT / Path(path_value.replace("/", "\\"))


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


def load_protocol_manifest(state: ValidationState) -> dict[str, Any] | None:
    if not PROTOCOL_MANIFEST_PATH.is_file():
        state.add("ERROR", "protocol manifest missing: packages/character-system/shared/protocol_manifest.json")
        return None

    try:
        data = json.loads(PROTOCOL_MANIFEST_PATH.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        state.add("ERROR", f"protocol manifest is not valid JSON: {exc}")
        return None

    required_top_level = [
        "protocol_manifest_version",
        "shared_protocols",
        "runtime_loop_templates",
        "runtime_loop_ledgers",
        "core_skills",
    ]
    for key in required_top_level:
        if key not in data:
            state.add("ERROR", f"protocol manifest missing top-level field: {key}")

    for key in [
        "shared_protocols",
        "runtime_loop_templates",
        "runtime_loop_ledgers",
        "core_skills",
    ]:
        if key in data and not isinstance(data[key], list):
            state.add("ERROR", f"protocol manifest field must be a list: {key}")

    state.add("INFO", "protocol manifest loaded")
    return data


def required_entry_fields(entry: Any, fields: list[str], label: str, state: ValidationState) -> bool:
    if not isinstance(entry, dict):
        state.add("ERROR", f"{label} entry must be an object")
        return False

    ok = True
    for field in fields:
        if field not in entry:
            state.add("ERROR", f"{label} entry missing field: {field}")
            ok = False
    return ok


def check_path_entry(
    entry: dict[str, Any],
    label: str,
    state: ValidationState,
    sink: list[dict[str, Any]],
) -> None:
    path_value = str(entry.get("path", ""))
    path = resolve_workspace_path(path_value)
    exists = path.is_file()
    required = bool(entry.get("required", False))

    sink.append(
        {
            "id": entry.get("id", ""),
            "path": path_value,
            "required": required,
            "exists": exists,
        }
    )

    if exists:
        state.add("INFO", f"{label} exists: {path_value}")
    elif required:
        state.add("ERROR", f"required {label} missing: {path_value}")
    else:
        state.add("WARNING", f"optional {label} missing: {path_value}")


def check_registered_paths(manifest: dict[str, Any], state: ValidationState) -> None:
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()

    for entry in manifest.get("shared_protocols", []):
        if not required_entry_fields(entry, ["id", "path", "required", "used_by"], "shared_protocol", state):
            continue
        entry_id = str(entry["id"])
        entry_path = str(entry["path"])
        if entry_id in seen_ids:
            state.add("WARNING", f"duplicate shared protocol id: {entry_id}")
        if entry_path in seen_paths:
            state.add("WARNING", f"duplicate shared protocol path: {entry_path}")
        seen_ids.add(entry_id)
        seen_paths.add(entry_path)
        if not isinstance(entry.get("used_by"), list):
            state.add("WARNING", f"shared protocol used_by should be a list: {entry_id}")
        check_path_entry(entry, "shared protocol", state, state.checked_protocols)

    for entry in manifest.get("runtime_loop_templates", []):
        if not required_entry_fields(entry, ["id", "path", "required"], "runtime_loop_template", state):
            continue
        check_path_entry(entry, "runtime loop template", state, state.checked_templates)

    for entry in manifest.get("runtime_loop_ledgers", []):
        if not required_entry_fields(entry, ["id", "path", "required"], "runtime_loop_ledger", state):
            continue
        check_path_entry(entry, "runtime loop ledger", state, state.checked_ledgers)


def check_core_skills(manifest: dict[str, Any], state: ValidationState) -> None:
    registered_protocol_paths = {
        str(entry.get("path", ""))
        for entry in manifest.get("shared_protocols", [])
        if isinstance(entry, dict)
    }
    shared_protocol_basenames = {
        Path(path).name for path in registered_protocol_paths if path
    }

    for entry in manifest.get("core_skills", []):
        if not required_entry_fields(entry, ["id", "path", "required_shared_protocols"], "core_skill", state):
            continue

        skill_id = str(entry["id"])
        skill_path_value = str(entry["path"])
        skill_path = resolve_workspace_path(skill_path_value)
        shared_protocols_path = skill_path / "SHARED_PROTOCOLS.md"
        required_protocols = entry.get("required_shared_protocols", [])
        if not isinstance(required_protocols, list):
            state.add("ERROR", f"core skill required_shared_protocols must be a list: {skill_id}")
            required_protocols = []

        skill_result = {
            "id": skill_id,
            "path": skill_path_value,
            "exists": skill_path.is_dir(),
            "shared_protocols_file": rel_path(shared_protocols_path),
            "shared_protocols_exists": shared_protocols_path.is_file(),
            "required_refs": len(required_protocols),
            "missing_refs": [],
            "unclear_refs": [],
        }

        if not skill_path.is_dir():
            state.add("ERROR", f"required core skill missing: {skill_path_value}")
            state.checked_skills.append(skill_result)
            continue

        if not shared_protocols_path.is_file():
            state.add("ERROR", f"required SHARED_PROTOCOLS.md missing for {skill_id}")
            state.checked_skills.append(skill_result)
            continue

        content = shared_protocols_path.read_text(encoding="utf-8-sig", errors="replace")
        normalized_content = content.replace("\\", "/")

        for protocol_path in required_protocols:
            protocol_path = str(protocol_path)
            if protocol_path not in registered_protocol_paths:
                state.add(
                    "WARNING",
                    f"{skill_id} requires protocol not registered in packages/character-system/shared/protocol_manifest.json: {protocol_path}",
                )
            if protocol_path in normalized_content:
                continue

            basename = Path(protocol_path).name
            if basename in normalized_content:
                skill_result["unclear_refs"].append(protocol_path)
                state.add(
                    "WARNING",
                    f"{skill_id} mentions {basename} but not the canonical path {protocol_path}",
                )
            else:
                skill_result["missing_refs"].append(protocol_path)
                state.add(
                    "ERROR",
                    f"{skill_id} SHARED_PROTOCOLS.md missing required protocol reference: {protocol_path}",
                )

        check_local_shared_duplicates(skill_id, skill_path, shared_protocol_basenames, state)
        state.checked_skills.append(skill_result)
        state.add("INFO", f"core skill checked: {skill_id}")


def check_local_shared_duplicates(
    skill_id: str,
    skill_path: Path,
    shared_protocol_basenames: set[str],
    state: ValidationState,
) -> None:
    local_shared_dir = skill_path / "shared"
    if local_shared_dir.exists():
        state.add("WARNING", f"{skill_id} contains a local shared/ directory")

    for file_path in skill_path.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.name == "SHARED_PROTOCOLS.md":
            continue
        if ".git" in file_path.parts:
            continue
        if file_path.name in shared_protocol_basenames:
            state.add(
                "WARNING",
                f"{skill_id} may contain a local duplicate of shared protocol {file_path.name}: {rel_path(file_path)}",
            )


def check_schema_status(state: ValidationState) -> None:
    schema_paths = [
        "packages/character-system/shared/schemas/protocol_manifest.schema.json",
        "packages/character-system/shared/schemas/diagnosis_packet.schema.json",
        "packages/character-system/shared/schemas/handoff_packet.schema.json",
        "packages/character-system/shared/schemas/patch_note.schema.json",
        "packages/character-system/shared/schemas/validation_note.schema.json",
        "packages/character-system/shared/schemas/generalization_note.schema.json",
    ]

    for path_value in schema_paths:
        path = resolve_workspace_path(path_value)
        exists = path.is_file()
        valid_json = False
        if exists:
            try:
                json.loads(path.read_text(encoding="utf-8-sig"))
                valid_json = True
            except json.JSONDecodeError as exc:
                state.add("ERROR", f"schema is not valid JSON: {path_value}: {exc}")

        state.schema_status.append(
            {
                "path": path_value,
                "exists": exists,
                "valid_json": valid_json,
            }
        )

        if not exists:
            state.add("ERROR", f"required schema missing: {path_value}")
        elif valid_json:
            state.add("INFO", f"schema present: {path_value}")

    state.add(
        "WARNING",
        "schemas are present as lightweight field contracts; deep instance validation is not yet enforced",
    )


def check_report_staleness(state: ValidationState) -> None:
    if not REPORT_PATH.exists():
        return

    report_mtime = REPORT_PATH.stat().st_mtime
    staleness_sources = [
        PROTOCOL_MANIFEST_PATH,
        Path(__file__),
        *[resolve_workspace_path(item["path"]) for item in state.checked_protocols],
    ]
    newer = [path for path in staleness_sources if path.exists() and path.stat().st_mtime > report_mtime]
    if newer:
        state.add(
            "WARNING",
            "previous protocol validation report was stale before this run",
        )


def markdown_table(rows: list[dict[str, Any]], headers: list[str]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        values = [str(row.get(header, "")) for header in headers]
        lines.append("| " + " | ".join(values) + " |")
    return lines


def finding_lines(findings: list[Finding]) -> list[str]:
    if not findings:
        return ["- None."]
    return [f"- {finding.severity}: {finding.message}" for finding in findings]


def write_report(manifest: dict[str, Any] | None, state: ValidationState) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    source_commit = get_source_commit()
    protocol_count = len(manifest.get("shared_protocols", [])) if manifest else 0
    skill_count = len(manifest.get("core_skills", [])) if manifest else 0
    template_count = len(manifest.get("runtime_loop_templates", [])) if manifest else 0
    ledger_count = len(manifest.get("runtime_loop_ledgers", [])) if manifest else 0

    lines: list[str] = [
        "---",
        "report_name: protocol_validation_report",
        f"generated_at: {now}",
        "generated_by: scripts/validate_protocols.py",
        f"source_root: {WORKSPACE_ROOT}",
        f"manifest_path: {WORKSPACE_MANIFEST_PATH}",
        f"protocol_manifest_path: {PROTOCOL_MANIFEST_PATH}",
        f"source_commit: {source_commit}",
        "report_scope: character-system protocol contract validation",
        "report_is_snapshot: true",
        "truth_source:",
        "  - workspace_manifest.yaml",
        "  - packages/character-system/shared/protocol_manifest.json",
        "  - shared/",
        "  - current git commit",
        "---",
        "",
        "Report is a snapshot. Manifest and shared protocol sources are the source of truth. If this report conflicts with source files, trust the source files and rerun validation.",
        "",
        "# Protocol Validation Report",
        "",
        "## 1. Summary",
        "",
        f"- Errors: `{len(state.errors)}`",
        f"- Warnings: `{len(state.warnings)}`",
        f"- Info: `{len(state.info)}`",
        f"- Package and workspace protocol dependencies checked: `{protocol_count}`",
        f"- Core skills checked: `{skill_count}`",
        f"- Runtime loop templates checked: `{template_count}`",
        f"- Runtime loop ledgers checked: `{ledger_count}`",
        "",
        "## 2. Errors",
        "",
        *finding_lines(state.errors),
        "",
        "## 3. Warnings",
        "",
        *finding_lines(state.warnings),
        "",
        "## 4. Checked Protocol Dependencies",
        "",
        *markdown_table(state.checked_protocols, ["id", "path", "required", "exists"]),
        "",
        "## 5. Checked Core Skills",
        "",
        *markdown_table(
            state.checked_skills,
            [
                "id",
                "path",
                "exists",
                "shared_protocols_exists",
                "required_refs",
                "missing_refs",
                "unclear_refs",
            ],
        ),
        "",
        "## 6. Checked Runtime Loop Templates",
        "",
        *markdown_table(state.checked_templates, ["id", "path", "required", "exists"]),
        "",
        "## 7. Checked Ledgers",
        "",
        *markdown_table(state.checked_ledgers, ["id", "path", "required", "exists"]),
        "",
        "## 8. Schema Status",
        "",
        *markdown_table(state.schema_status, ["path", "exists", "valid_json"]),
        "",
        "## 9. Next Recommendations",
        "",
        "- Run `python scripts/validate_protocols.py` after changing `shared/`, runtime-loop templates, ledgers, or core skill `SHARED_PROTOCOLS.md` files.",
        "- Keep schema enforcement lightweight until runtime-loop packet instances need automated validation.",
        "- Treat warnings as review prompts; only errors should block protocol contract changes.",
    ]

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    state = ValidationState()
    manifest = load_protocol_manifest(state)

    if manifest is not None:
        check_registered_paths(manifest, state)
        check_core_skills(manifest, state)
        check_schema_status(state)
        check_report_staleness(state)

        state.add("INFO", f"protocol count: {len(manifest.get('shared_protocols', []))}")
        state.add("INFO", f"skill count: {len(manifest.get('core_skills', []))}")
        state.add("INFO", f"template count: {len(manifest.get('runtime_loop_templates', []))}")
        state.add("INFO", f"ledger count: {len(manifest.get('runtime_loop_ledgers', []))}")

    write_report(manifest, state)

    print(f"Protocol validation report: {rel_path(REPORT_PATH)}")
    print(f"ERROR: {len(state.errors)}")
    print(f"WARNING: {len(state.warnings)}")
    print(f"INFO: {len(state.info)}")

    for finding in state.errors:
        print(f"ERROR: {finding.message}")
    for finding in state.warnings:
        print(f"WARNING: {finding.message}")

    return 1 if state.errors else 0


if __name__ == "__main__":
    sys.exit(main())
