#!/usr/bin/env python3
"""Validate workspace_manifest.yaml for portability and consistency."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


WORKSPACE_ROOT = Path.cwd()
MANIFEST_PATH = WORKSPACE_ROOT / "workspace_manifest.yaml"
REPORT_PATH = WORKSPACE_ROOT / "reports" / "manifest_validation_report.md"


@dataclass
class Finding:
    severity: str
    message: str


class State:
    def __init__(self) -> None:
        self.errors: list[Finding] = []
        self.warnings: list[Finding] = []
        self.info: list[Finding] = []
        self.path_checks: list[dict[str, Any]] = []
        self.projection_checks: list[dict[str, Any]] = []
        self.absolute_fields: list[dict[str, str]] = []
        self.relative_candidates: list[dict[str, str]] = []

    def add(self, severity: str, message: str) -> None:
        finding = Finding(severity, message)
        if severity == "ERROR":
            self.errors.append(finding)
        elif severity == "WARNING":
            self.warnings.append(finding)
        else:
            self.info.append(finding)


def load_manifest(state: State) -> dict[str, Any] | None:
    if not MANIFEST_PATH.is_file():
        state.add("ERROR", "workspace_manifest.yaml is missing")
        return None
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        state.add("ERROR", f"workspace_manifest.yaml is not parseable JSON-compatible YAML: {exc}")
        return None
    state.add("INFO", "workspace_manifest.yaml parsed")
    return manifest


def resolve_path(workspace_root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return workspace_root / Path(value.replace("/", "\\"))


def path_exists(path: Path, expect_dir: bool | None = None) -> bool:
    if expect_dir is True:
        return path.is_dir()
    if expect_dir is False:
        return path.is_file()
    return path.exists()


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


def check_required_fields(manifest: dict[str, Any], state: State) -> None:
    top = [
        "workspace",
        "platform_roots",
        "session_stores",
        "output_roots",
        "shared",
        "packages",
        "skills",
        "projections",
        "protocols",
        "discovery",
        "failure_policy",
    ]
    for key in top:
        if key not in manifest:
            state.add("ERROR", f"manifest missing top-level field: {key}")

    workspace = manifest.get("workspace", {})
    for key in ["workspace_name", "workspace_version", "source_of_truth", "manifest_path"]:
        if key not in workspace:
            state.add("ERROR", f"manifest workspace metadata missing field: {key}")

    if "required_missing" not in manifest.get("failure_policy", {}):
        state.add("ERROR", "failure_policy.required_missing is missing")
    if "optional_missing" not in manifest.get("failure_policy", {}):
        state.add("ERROR", "failure_policy.optional_missing is missing")

    session_stores = manifest.get("session_stores", {})
    for tool in ("claude", "opencode"):
        store = session_stores.get(tool)
        if not isinstance(store, dict):
            state.add("ERROR", f"session_stores.{tool} must be an object")
            continue
        data_root = str(store.get("data_root", ""))
        if not data_root or not Path(data_root).is_absolute():
            state.add("ERROR", f"session_stores.{tool}.data_root must be an absolute local path")

    workspace_output_root = str(manifest.get("output_roots", {}).get("workspace", ""))
    if not workspace_output_root or not Path(workspace_output_root).is_absolute():
        state.add("ERROR", "output_roots.workspace must be an absolute local path")

    discovery = manifest.get("discovery", {})
    if "max_parent_depth" not in discovery:
        state.add("ERROR", "discovery.max_parent_depth is missing")
    if "forbidden" not in discovery:
        state.add("ERROR", "discovery.forbidden is missing")

    valid_roles = {
        "production",
        "maintenance",
        "feedback_diagnosis",
        "runtime_character",
        "governance",
    }
    valid_authorities = {
        "runtime_output_only",
        "diagnosis_text_only",
        "diagnosis_record_write",
        "source_patch",
        "generator_write",
        "environment_audit",
        "environment_migration_apply",
    }
    valid_execution_modes = {
        "text_only",
        "record_write",
        "source_patch",
        "environment_write",
    }
    projection_ids = {
        str(item.get("id", ""))
        for item in manifest.get("projections", [])
        if isinstance(item, dict)
    }
    package_ids: set[str] = set()
    for package in manifest.get("packages", []):
        if not isinstance(package, dict):
            state.add("ERROR", "packages entries must be objects")
            continue
        package_id = str(package.get("id", ""))
        if not package_id:
            state.add("ERROR", "package id is missing")
        elif package_id in package_ids:
            state.add("ERROR", f"duplicate package id: {package_id}")
        package_ids.add(package_id)

    for skill in manifest.get("skills", []):
        skill_id = str(skill.get("id", ""))
        package_id = str(skill.get("package_id", ""))
        if package_id and package_id not in package_ids:
            state.add("ERROR", f"skills[{skill_id}] uses unknown package_id: {package_id}")
        protocol_dependencies = skill.get("protocol_dependencies", [])
        if not isinstance(protocol_dependencies, list):
            state.add("ERROR", f"skills[{skill_id}].protocol_dependencies must be a list")
        role = skill.get("role")
        if role not in valid_roles:
            state.add("ERROR", f"skills[{skill_id}].role is missing or invalid: {role}")

        authority = skill.get("authority")
        check_mode_contract(
            authority,
            valid_authorities,
            f"skills[{skill_id}].authority",
            state,
        )
        execution_modes = skill.get("execution_modes")
        check_mode_contract(
            execution_modes,
            valid_execution_modes,
            f"skills[{skill_id}].execution_modes",
            state,
        )

        exposures = skill.get("exposures")
        if not isinstance(exposures, list) or not exposures:
            state.add("ERROR", f"skills[{skill_id}].exposures must be a non-empty list")
            continue
        seen_platforms: set[str] = set()
        for exposure in exposures:
            if not isinstance(exposure, dict):
                state.add("ERROR", f"skills[{skill_id}].exposures entries must be objects")
                continue
            platform = str(exposure.get("platform", ""))
            projection_id = str(exposure.get("projection_id", ""))
            if platform not in manifest.get("platform_roots", {}):
                state.add("ERROR", f"skills[{skill_id}] exposure uses unknown platform: {platform}")
            if projection_id not in projection_ids:
                state.add("ERROR", f"skills[{skill_id}] exposure references unknown projection: {projection_id}")
            if platform in seen_platforms:
                state.add("WARNING", f"skills[{skill_id}] has multiple exposures for platform: {platform}")
            seen_platforms.add(platform)

    plugin_skills = manifest.get("plugin_skills", [])
    if not isinstance(plugin_skills, list):
        state.add("ERROR", "manifest plugin_skills must be a list")
    else:
        seen_plugin_ids: set[str] = set()
        for plugin_skill in plugin_skills:
            if not isinstance(plugin_skill, dict):
                state.add("ERROR", "plugin_skills entries must be objects")
                continue
            skill_id = str(plugin_skill.get("id", ""))
            qualified_id = str(plugin_skill.get("qualified_id", ""))
            plugin_id = str(plugin_skill.get("plugin_id", ""))
            if not skill_id or not qualified_id or not plugin_id:
                state.add(
                    "ERROR",
                    "plugin_skills entries require id, qualified_id, and plugin_id",
                )
            if skill_id in seen_plugin_ids:
                state.add("ERROR", f"duplicate plugin skill id: {skill_id}")
            seen_plugin_ids.add(skill_id)
            if plugin_skill.get("role") not in valid_roles:
                state.add(
                    "ERROR",
                    f"plugin_skills[{skill_id}].role is missing or invalid: "
                    f"{plugin_skill.get('role')}",
                )
            check_mode_contract(
                plugin_skill.get("execution_modes"),
                valid_execution_modes,
                f"plugin_skills[{skill_id}].execution_modes",
                state,
            )


def check_mode_contract(
    contract: Any,
    valid_values: set[str],
    label: str,
    state: State,
) -> None:
    if not isinstance(contract, dict):
        state.add("ERROR", f"{label} must be an object with default and allowed")
        return
    default = contract.get("default")
    allowed = contract.get("allowed")
    if default not in valid_values:
        state.add("ERROR", f"{label}.default is missing or invalid: {default}")
    if not isinstance(allowed, list) or not allowed:
        state.add("ERROR", f"{label}.allowed must be a non-empty list")
        return
    invalid = [value for value in allowed if value not in valid_values]
    if invalid:
        state.add("ERROR", f"{label}.allowed contains invalid values: {invalid}")
    if default not in allowed:
        state.add("ERROR", f"{label}.default must also appear in allowed")


def check_paths(manifest: dict[str, Any], state: State) -> None:
    workspace_root = Path(str(manifest.get("workspace", {}).get("source_of_truth", WORKSPACE_ROOT))).resolve()

    source_of_truth = Path(str(manifest.get("workspace", {}).get("source_of_truth", "")))
    if source_of_truth.resolve() != WORKSPACE_ROOT.resolve():
        state.add(
            "WARNING",
            f"workspace.source_of_truth does not match current working directory: {source_of_truth} vs {WORKSPACE_ROOT}",
        )
    else:
        state.add("INFO", "workspace.source_of_truth matches current working directory")

    shared = manifest.get("shared", {})
    shared_source = resolve_path(workspace_root, str(shared.get("source_path", "")))
    record_path_check(state, "shared.source_path", str(shared.get("source_path", "")), shared_source, True, True)

    package_protocol_ids: dict[str, set[str]] = {}
    for package in manifest.get("packages", []):
        if not isinstance(package, dict):
            continue
        package_id = str(package.get("id", ""))
        for field in (
            "source_path",
            "runtime_path",
            "engineering_path",
            "shared_path",
            "reports_path",
        ):
            declared = str(package.get(field, ""))
            resolved = resolve_path(workspace_root, declared)
            record_path_check(
                state,
                f"packages[{package_id}].{field}",
                declared,
                resolved,
                True,
                True,
            )
        protocol_manifest_value = str(package.get("protocol_manifest", ""))
        protocol_manifest_path = resolve_path(workspace_root, protocol_manifest_value)
        record_path_check(
            state,
            f"packages[{package_id}].protocol_manifest",
            protocol_manifest_value,
            protocol_manifest_path,
            False,
            True,
        )
        protocol_ids: set[str] = set()
        if protocol_manifest_path.is_file():
            try:
                package_manifest = json.loads(
                    protocol_manifest_path.read_text(encoding="utf-8-sig")
                )
                protocol_ids = {
                    str(entry.get("id", ""))
                    for entry in package_manifest.get("shared_protocols", [])
                    if isinstance(entry, dict)
                }
            except json.JSONDecodeError as exc:
                state.add(
                    "ERROR",
                    f"package protocol manifest is not valid JSON: {package_id}: {exc}",
                )
        package_protocol_ids[package_id] = protocol_ids

    for skill in manifest.get("skills", []):
        skill_id = str(skill.get("id", ""))
        package_id = str(skill.get("package_id", ""))
        skill_source = resolve_path(workspace_root, str(skill.get("source_path", "")))
        record_path_check(state, f"skills[{skill_id}].source_path", str(skill.get("source_path", "")), skill_source, True, True)
        if package_id:
            registered_ids = package_protocol_ids.get(package_id, set())
            for protocol_id in skill.get("protocol_dependencies", []):
                if str(protocol_id) not in registered_ids:
                    state.add(
                        "ERROR",
                        f"skills[{skill_id}] references unregistered package protocol: {protocol_id}",
                    )
        for rel in skill.get("required_files", []):
            required_path = resolve_path(skill_source, str(rel))
            record_path_check(state, f"skills[{skill_id}].required_files:{rel}", str(rel), required_path, None, True)

    for protocol in manifest.get("protocols", []):
        protocol_id = str(protocol.get("id", ""))
        protocol_path = resolve_path(workspace_root, str(protocol.get("path", "")))
        record_path_check(state, f"protocols[{protocol_id}].path", str(protocol.get("path", "")), protocol_path, False, bool(protocol.get("required", False)))

    projections_by_id = {
        str(projection.get("id", "")): projection
        for projection in manifest.get("projections", [])
        if isinstance(projection, dict)
    }
    expected_targets_by_projection: dict[str, str] = {}
    for skill in manifest.get("skills", []):
        skill_id = str(skill.get("id", ""))
        source_path = str(skill.get("source_path", ""))
        skill_source = resolve_path(workspace_root, source_path)
        exposures = skill.get("exposures", [])
        for exposure in exposures if isinstance(exposures, list) else []:
            if not isinstance(exposure, dict):
                continue
            projection_id = str(exposure.get("projection_id", ""))
            projection = projections_by_id.get(projection_id, {})
            if projection and str(projection.get("platform", "")) != str(exposure.get("platform", "")):
                state.add(
                    "ERROR",
                    f"skills[{skill_id}] exposure platform does not match projection {projection_id}",
                )
            expected_targets_by_projection[projection_id] = source_path

        if exposures:
            primary = exposures[0]
            primary_projection = projections_by_id.get(str(primary.get("projection_id", "")), {})
            legacy_platform = str(skill.get("platform", ""))
            legacy_projection_path = str(skill.get("projection_path", ""))
            if legacy_platform != str(primary.get("platform", "")):
                state.add(
                    "ERROR",
                    f"skills[{skill_id}].platform must match the first exposure during compatibility phase",
                )
            if legacy_projection_path != str(primary_projection.get("link_path", "")):
                state.add(
                    "ERROR",
                    f"skills[{skill_id}].projection_path must match the first exposure during compatibility phase",
                )

        skill_entrypoint = skill_source / "SKILL.md"
        if skill_entrypoint.is_file():
            frontmatter_name = read_frontmatter_name(skill_entrypoint)
            if not frontmatter_name:
                state.add(
                    "ERROR",
                    f"skill entrypoint is missing frontmatter name: {skill_id}",
                )
            elif frontmatter_name != skill_id:
                state.add(
                    "ERROR",
                    f"skill id/frontmatter name conflict: {skill_id} vs {frontmatter_name}",
                )
    for platform in manifest.get("platform_roots", {}).keys():
        expected_targets_by_projection[f"{platform}.shared"] = str(shared.get("source_path", ""))

    for projection in manifest.get("projections", []):
        projection_id = str(projection.get("id", ""))
        if projection_id not in expected_targets_by_projection:
            state.add("WARNING", f"projection is not referenced by any skill exposure: {projection_id}")
        link_path = resolve_path(workspace_root, str(projection.get("link_path", "")))
        target_path = resolve_path(workspace_root, str(projection.get("target_path", "")))
        target_exists = target_path.is_dir()
        link_exists = link_path.exists()
        expected_target_value = expected_targets_by_projection.get(projection_id, str(projection.get("target_path", "")))
        target_expected = resolve_path(workspace_root, expected_target_value).resolve()
        source_match = target_path.resolve() == target_expected
        state.projection_checks.append(
            {
                "id": projection_id,
                "link_path": str(link_path),
                "target_path": str(target_path),
                "link_exists": link_exists,
                "target_exists": target_exists,
                "target_matches_source": source_match,
            }
        )
        if not target_exists and projection.get("required", False):
            state.add("ERROR", f"required projection target missing: {projection_id} -> {target_path}")
        if not source_match:
            state.add(
                "ERROR",
                f"projection target does not match manifest source path: {projection_id} declares {projection.get('target_path')} expected {expected_target_value}",
            )
        if link_exists:
            state.add("INFO", f"projection link path exists: {projection_id}")
        else:
            state.add("WARNING", f"projection link path missing: {projection_id} -> {link_path}")


def read_frontmatter_name(path: Path) -> str:
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if stripped.startswith("name:"):
            return stripped.split(":", 1)[1].strip().strip("\"'")
    return ""


def record_path_check(
    state: State,
    field: str,
    declared: str,
    resolved: Path,
    expect_dir: bool | None,
    required: bool,
) -> None:
    exists = path_exists(resolved, expect_dir)
    state.path_checks.append(
        {
            "field": field,
            "declared": declared,
            "resolved": str(resolved),
            "required": required,
            "exists": exists,
        }
    )
    if exists:
        state.add("INFO", f"path exists: {field}")
    elif required:
        state.add("ERROR", f"required path missing: {field} -> {resolved}")
    else:
        state.add("WARNING", f"optional path missing: {field} -> {resolved}")


def check_absolute_paths(manifest: dict[str, Any], state: State) -> None:
    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                walk(child, f"{path}.{key}" if path else str(key))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")
        elif isinstance(value, str) and Path(value).is_absolute():
            allowed = (
                path == "workspace.source_of_truth"
                or path.startswith("platform_roots.")
                or path.startswith("session_stores.")
                or path.startswith("output_roots.")
                or path.startswith("shared.projection_paths.")
                or path.endswith(".projection_path")
                or path.endswith(".link_path")
            )
            state.absolute_fields.append({"field": path, "value": value, "allowed": str(allowed)})
            if allowed:
                state.add("INFO", f"explained absolute path field: {path}")
            else:
                state.add("WARNING", f"absolute path field may need portability review: {path}")

    walk(manifest, "")

    for skill in manifest.get("skills", []):
        projection_path = str(skill.get("projection_path", ""))
        if Path(projection_path).is_absolute():
            state.relative_candidates.append(
                {
                    "field": f"skills[{skill.get('id')}].projection_path",
                    "reason": "can be derived from platform_roots plus skill id when scripts support it",
                }
            )

    for projection in manifest.get("projections", []):
        link_path = str(projection.get("link_path", ""))
        if Path(link_path).is_absolute():
            state.relative_candidates.append(
                {
                    "field": f"projections[{projection.get('id')}].link_path",
                    "reason": "platform-local deployment path; could be templated from platform_roots in a future manifest version",
                }
            )


def markdown_table(rows: list[dict[str, Any]], headers: list[str]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return lines


def finding_lines(findings: list[Finding]) -> list[str]:
    if not findings:
        return ["- None."]
    return [f"- {finding.severity}: {finding.message}" for finding in findings]


def write_report(state: State) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    lines = [
        "---",
        "report_name: manifest_validation_report",
        f"generated_at: {now}",
        "generated_by: scripts/validate_manifest.py",
        f"source_root: {WORKSPACE_ROOT}",
        f"manifest_path: {MANIFEST_PATH}",
        f"source_commit: {get_source_commit()}",
        "report_scope: manifest portability and consistency validation",
        "report_is_snapshot: true",
        "truth_source:",
        "  - workspace_manifest.yaml",
        "  - shared/",
        "  - current git commit",
        "---",
        "",
        "Report is a snapshot. Manifest is the source of truth. If this report conflicts with the manifest, trust the manifest and rerun validation.",
        "",
        "# Manifest Validation Report",
        "",
        "## Summary",
        "",
        f"- Errors: `{len(state.errors)}`",
        f"- Warnings: `{len(state.warnings)}`",
        f"- Info: `{len(state.info)}`",
        "",
        "## Errors",
        "",
        *finding_lines(state.errors),
        "",
        "## Warnings",
        "",
        *finding_lines(state.warnings),
        "",
        "## Path Checks",
        "",
        *markdown_table(state.path_checks, ["field", "declared", "resolved", "required", "exists"]),
        "",
        "## Projection Checks",
        "",
        *markdown_table(state.projection_checks, ["id", "link_path", "target_path", "link_exists", "target_exists", "target_matches_source"]),
        "",
        "## Absolute Path Fields",
        "",
        *markdown_table(state.absolute_fields, ["field", "value", "allowed"]),
        "",
        "## Future Relative Candidates",
        "",
        *markdown_table(state.relative_candidates, ["field", "reason"]),
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    state = State()
    manifest = load_manifest(state)
    if manifest is not None:
        check_required_fields(manifest, state)
        check_paths(manifest, state)
        check_absolute_paths(manifest, state)
    write_report(state)
    print(f"Manifest validation report: {REPORT_PATH.relative_to(WORKSPACE_ROOT).as_posix()}")
    print(f"ERROR: {len(state.errors)}")
    print(f"WARNING: {len(state.warnings)}")
    for finding in state.errors:
        print(f"ERROR: {finding.message}")
    for finding in state.warnings:
        print(f"WARNING: {finding.message}")
    return 1 if state.errors else 0


if __name__ == "__main__":
    sys.exit(main())
