#!/usr/bin/env python3
"""Resolve one task into bounded context, prompt guidance, and token estimates."""

from __future__ import annotations

import argparse
import datetime
import fnmatch
import json
import math
import os
import re
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError:  # pragma: no cover - exercised through CLI failure behavior
    yaml = None


DEFAULT_MAX_PARENT_DEPTH = 5
DEFAULT_MANIFEST_FILENAME = "workspace_manifest.yaml"
TASK_REGISTRY_PATH = "PROJECT_CONTEXT/task_registry.yaml"
PROMPT_REGISTRY_PATH = "USAGE_GUIDES/prompt_registry.yaml"
PLACEHOLDER_RE = re.compile(r"<([A-Za-z0-9_-]+)>")
PATH_SUFFIXES = {
    ".cfg",
    ".css",
    ".csv",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".toml",
    ".ts",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
COMMAND_PREFIXES = (
    "git ",
    "python ",
    "powershell ",
    "pwsh ",
    "opencode ",
    "opencode:",
)
TASK_GROUPS = (
    (
        "Governance and Runtime Authority",
        (
            "agent_governance_update",
            "runtime_authorization_enforcement",
            "governance_workflow_simplification",
            "claude_project_boundary",
            "platform_exposure",
        ),
    ),
    (
        "Developer Workflow Tooling",
        (
            "developer_interface_tooling",
            "workspace_developer_experience",
            "workspace_health_tooling",
            "workspace_launcher_tooling",
            "context_resolution_tooling",
            "failure_diagnostics_tooling",
            "change_surface_planning",
            "change_scope_verification",
            "governance_summary_tooling",
        ),
    ),
    (
        "Knowledge, Prompts, and Documentation",
        (
            "project_memory_maintenance",
            "startup_context_optimization",
            "knowledge_interface_tooling",
            "workspace_engineering_knowledge",
            "prompt_usage_update",
            "source_of_truth_dedup",
            "task_registry_update",
            "shared_policy_update",
        ),
    ),
    (
        "Skills and Packages",
        (
            "skill_lifecycle_tooling",
            "skill_release_packaging",
            "skill_architecture_update",
            "skill_metadata_update",
            "runtime_drift_fix",
        ),
    ),
    (
        "Reports, Freshness, and Migration",
        (
            "report_regeneration",
            "report_freshness_tooling",
            "cleanup_migration",
            "session_continuity",
        ),
    ),
)


@dataclass
class CountedFile:
    path: str
    bytes: int
    tokens: int
    method: str
    source: str


@dataclass
class ResourceFinding:
    severity: str
    resource_class: str
    reason: str
    resource: str
    expected: str
    discovery_attempts: list[str]
    action: str
    impact: str | None = None


class TokenCounter:
    def __init__(self, encoding_name: str) -> None:
        self.encoding_name = encoding_name
        self.method = "heuristic"
        self.exact = False
        self._encoding = None
        try:
            import tiktoken

            self._encoding = tiktoken.get_encoding(encoding_name)
            self.method = f"tiktoken:{encoding_name}"
            self.exact = True
        except (ImportError, ValueError):
            self.method = "heuristic:ascii_chars_div_4_plus_non_ascii_chars"

    def count(self, text: str) -> int:
        if self._encoding is not None:
            return len(self._encoding.encode(text))
        ascii_count = sum(1 for char in text if ord(char) < 128)
        non_ascii_count = len(text) - ascii_count
        return math.ceil(ascii_count / 4) + non_ascii_count


def find_manifest(start: Path, filename: str, max_depth: int) -> Path | None:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for _depth in range(max_depth + 1):
        candidate = current / filename
        if candidate.is_file():
            return candidate
        if current.parent == current:
            break
        current = current.parent
    return None


def load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError(
            "PyYAML is required. Install scripts/requirements-context-tools.txt."
        )
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"failed to load YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"expected a mapping at document root: {path}")
    return data


def parse_bindings(values: list[str]) -> dict[str, list[str]]:
    bindings: dict[str, list[str]] = {}
    for raw in values:
        if "=" not in raw:
            raise ValueError(f"binding must use name=value: {raw}")
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            raise ValueError(f"binding must use non-empty name=value: {raw}")
        bindings.setdefault(key, []).append(value)
    return bindings


def expand_placeholders(value: str, bindings: dict[str, list[str]]) -> tuple[list[str], set[str]]:
    placeholders = list(dict.fromkeys(PLACEHOLDER_RE.findall(value)))
    unresolved = {name for name in placeholders if name not in bindings}
    if unresolved:
        return [value], unresolved

    expanded = [value]
    for name in placeholders:
        next_values: list[str] = []
        for current in expanded:
            for replacement in bindings[name]:
                next_values.append(current.replace(f"<{name}>", replacement))
        expanded = next_values
    return expanded, set()


def expand_text_entries(
    entries: Iterable[str],
    bindings: dict[str, list[str]],
) -> tuple[list[str], set[str]]:
    expanded_entries: list[str] = []
    unresolved: set[str] = set()
    for entry in entries:
        expanded, missing = expand_placeholders(str(entry), bindings)
        expanded_entries.extend(expanded)
        unresolved.update(missing)
    return list(dict.fromkeys(expanded_entries)), unresolved


def looks_like_path(value: str) -> bool:
    stripped = value.strip()
    lower = stripped.lower()
    if lower.startswith(COMMAND_PREFIXES):
        return False
    if lower.startswith(("actual ", "explicit ", "all task ", "relevant ")):
        return False
    if stripped.startswith((".", "<")):
        return True
    if "/" in stripped or "\\" in stripped:
        return True
    return Path(stripped).suffix.lower() in PATH_SUFFIXES


def normalize_relative_path(workspace_root: Path, value: str) -> tuple[Path | None, str | None]:
    candidate = Path(value)
    resolved = candidate.resolve() if candidate.is_absolute() else (workspace_root / candidate).resolve()
    try:
        relative = resolved.relative_to(workspace_root.resolve())
    except ValueError:
        return None, f"path escapes workspace: {value}"
    return resolved, relative.as_posix()


def git_visible_files(workspace_root: Path) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=workspace_root,
            check=True,
            capture_output=True,
        )
        items = result.stdout.decode("utf-8", errors="surrogateescape").split("\0")
        return [
            (workspace_root / item).resolve()
            for item in items
            if item and (workspace_root / item).is_file()
        ]
    except (OSError, subprocess.CalledProcessError):
        return [
            path.resolve()
            for path in workspace_root.rglob("*")
            if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts
        ]


def path_pattern(value: str) -> str | None:
    stripped = value.strip().replace("\\", "/")
    if not looks_like_path(stripped):
        return None
    if " unless " in stripped:
        stripped = stripped.split(" unless ", 1)[0]
    return stripped


def matches_ignore(relative: str, ignore_entries: Iterable[str]) -> bool:
    normalized = relative.replace("\\", "/")
    for entry in ignore_entries:
        pattern = path_pattern(str(entry))
        if not pattern:
            continue
        pattern = pattern.lstrip("./")
        if pattern.endswith("/"):
            base = pattern.rstrip("/")
            if fnmatch.fnmatch(normalized, base) or fnmatch.fnmatch(normalized, f"{base}/**"):
                return True
        elif fnmatch.fnmatch(normalized, pattern) or fnmatch.fnmatch(normalized, f"{pattern}/**"):
            return True
    return False


def collect_files_for_entry(
    workspace_root: Path,
    entry: str,
    visible_files: list[Path],
    ignore_entries: list[str],
    resource_class: str,
) -> tuple[list[Path], list[ResourceFinding]]:
    findings: list[ResourceFinding] = []
    severity = "ERROR" if resource_class in {"required", "preloaded"} else "WARNING"
    resolved, relative = normalize_relative_path(workspace_root, entry)
    if resolved is None or relative is None:
        return [], [
            ResourceFinding(
                severity=severity,
                resource_class=resource_class,
                reason="path_escape",
                resource=entry,
                expected=f"a path contained by {workspace_root.resolve()}",
                discovery_attempts=[entry],
                action="correct the registry entry or binding; do not search outside the workspace",
                impact=(
                    "workflow stopped because a required resource escaped the workspace"
                    if severity == "ERROR"
                    else "continuing without this optional resource"
                ),
            )
        ]
    if matches_ignore(relative, ignore_entries):
        return [], [
            ResourceFinding(
                severity=severity,
                resource_class=resource_class,
                reason="ignored",
                resource=relative,
                expected=str(resolved),
                discovery_attempts=[str(resolved)],
                action=(
                    "remove the required path from ignore policy or correct the task registry"
                    if severity == "ERROR"
                    else "review the optional path only if this degraded context is needed"
                ),
                impact=(
                    "workflow stopped because a required resource is excluded by task policy"
                    if severity == "ERROR"
                    else "continuing without this optional resource"
                ),
            )
        ]
    if resolved.is_file():
        return [resolved], findings
    if resolved.is_dir():
        files: list[Path] = []
        for path in visible_files:
            try:
                child_relative = path.relative_to(workspace_root.resolve()).as_posix()
                path.relative_to(resolved)
            except ValueError:
                continue
            if not matches_ignore(child_relative, ignore_entries):
                files.append(path)
        return sorted(set(files)), findings
    return [], [
        ResourceFinding(
            severity=severity,
            resource_class=resource_class,
            reason="missing",
            resource=relative,
            expected=str(resolved),
            discovery_attempts=[str(resolved)],
            action=(
                "restore the missing resource or update the task registry if its location intentionally changed"
            ),
            impact=(
                "workflow stopped because the resource is required"
                if severity == "ERROR"
                else "continuing in degraded mode; related context may be unavailable"
            ),
        )
    ]


def format_resource_finding(finding: ResourceFinding) -> str:
    if finding.reason == "missing":
        label = (
            "Missing required resource"
            if finding.severity == "ERROR"
            else "Missing optional resource"
        )
    elif finding.reason == "ignored":
        label = (
            "Required resource excluded by task policy"
            if finding.severity == "ERROR"
            else "Optional resource excluded by task policy"
        )
    else:
        label = (
            "Required resource path blocked"
            if finding.severity == "ERROR"
            else "Optional resource path blocked"
        )

    lines = [
        f"[{finding.severity}]",
        f"{label}:",
        finding.resource,
        "",
        "Expected:",
        finding.expected,
        "",
        "Discovery attempts:",
        *[f"- {attempt}" for attempt in finding.discovery_attempts],
    ]
    if finding.impact:
        lines.extend(["", "Impact:", finding.impact])
    lines.extend(["", "Action:", finding.action])
    return "\n".join(lines)


def count_file(
    workspace_root: Path,
    path: Path,
    counter: TokenCounter,
    max_file_bytes: int,
    source: str,
) -> tuple[CountedFile | None, str | None]:
    relative = path.relative_to(workspace_root.resolve()).as_posix()
    try:
        size = path.stat().st_size
        if size > max_file_bytes:
            return None, f"skipped oversized file ({size} bytes): {relative}"
        raw = path.read_bytes()
    except OSError as exc:
        return None, f"could not read file {relative}: {exc}"
    if b"\x00" in raw:
        return None, f"skipped probable binary file: {relative}"
    text = raw.decode("utf-8-sig", errors="replace")
    return (
        CountedFile(
            path=relative,
            bytes=size,
            tokens=counter.count(text),
            method=counter.method,
            source=source,
        ),
        None,
    )


def resolve_entries(
    workspace_root: Path,
    entries: list[str],
    bindings: dict[str, list[str]],
    visible_files: list[Path],
    ignore_entries: list[str],
    consumed_files: set[str],
    retain_consumed: bool,
    resource_class: str,
) -> dict[str, Any]:
    paths: list[str] = []
    evidence: list[str] = []
    unresolved: set[str] = set()
    consumed: list[str] = []
    findings: list[ResourceFinding] = []
    files: list[Path] = []

    for entry in entries:
        expanded_values, missing = expand_placeholders(str(entry), bindings)
        if missing:
            unresolved.update(missing)
            paths.append(str(entry))
            continue
        for expanded in expanded_values:
            if not looks_like_path(expanded):
                evidence.append(expanded)
                continue
            normalized = expanded.replace("\\", "/").rstrip("/")
            if normalized in consumed_files and not retain_consumed:
                consumed.append(normalized)
                continue
            paths.append(expanded)
            entry_files, entry_findings = collect_files_for_entry(
                workspace_root,
                expanded,
                visible_files,
                ignore_entries,
                resource_class,
            )
            files.extend(entry_files)
            findings.extend(entry_findings)

    return {
        "paths": list(dict.fromkeys(paths)),
        "evidence": list(dict.fromkeys(evidence)),
        "unresolved": sorted(unresolved),
        "consumed": list(dict.fromkeys(consumed)),
        "findings": findings,
        "files": sorted(set(files)),
    }


def count_files(
    workspace_root: Path,
    files: list[Path],
    counter: TokenCounter,
    max_file_bytes: int,
    source: str,
) -> tuple[list[CountedFile], list[str]]:
    counted: list[CountedFile] = []
    warnings: list[str] = []
    for path in files:
        item, warning = count_file(workspace_root, path, counter, max_file_bytes, source)
        if item:
            counted.append(item)
        if warning:
            warnings.append(warning)
    return counted, warnings


def heading_slug(value: str) -> str:
    lowered = value.strip().lower()
    lowered = re.sub(r"[^\w\s-]", "", lowered, flags=re.UNICODE)
    return re.sub(r"[\s_-]+", "-", lowered).strip("-")


def extract_markdown_section(text: str, anchor: str) -> str:
    lines = text.splitlines()
    start_index: int | None = None
    start_level = 0
    for index, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match and heading_slug(match.group(2)) == anchor:
            start_index = index
            start_level = len(match.group(1))
            break
    if start_index is None:
        raise ValueError(f"markdown anchor not found: #{anchor}")

    end_index = len(lines)
    for index in range(start_index + 1, len(lines)):
        match = re.match(r"^(#{1,6})\s+", lines[index])
        if match and len(match.group(1)) <= start_level:
            end_index = index
            break
    return "\n".join(lines[start_index:end_index]).strip() + "\n"


def load_template_content(
    workspace_root: Path,
    template_reference: str,
) -> tuple[str, str]:
    path_value, separator, anchor = template_reference.partition("#")
    resolved, relative = normalize_relative_path(workspace_root, path_value)
    if resolved is None or relative is None:
        raise ValueError(f"template path escapes workspace: {path_value}")
    if not resolved.is_file():
        raise ValueError(f"template path not found: {relative}")
    text = resolved.read_text(encoding="utf-8-sig")
    if separator and anchor:
        return f"{relative}#{anchor}", extract_markdown_section(text, anchor)
    return relative, text


def merge_budget(defaults: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    merged = dict(defaults)
    task_budget = task.get("budget", {})
    if isinstance(task_budget, dict):
        merged.update(task_budget)
    return merged


def budget_status(initial_tokens: int, expanded_tokens: int | None, budget: dict[str, Any]) -> tuple[str, list[str]]:
    warnings: list[str] = []
    hard_max = budget.get("hard_max_tokens")
    selected_total = expanded_tokens if expanded_tokens is not None else initial_tokens
    if isinstance(hard_max, int) and selected_total > hard_max:
        return "HARD_LIMIT", [f"selected context exceeds hard_max_tokens ({selected_total} > {hard_max})"]

    required_warn = int(budget.get("required_warn_tokens", 0) or 0)
    expanded_warn = int(budget.get("expanded_warn_tokens", 0) or 0)
    if required_warn and initial_tokens > required_warn:
        warnings.append(f"initial context exceeds required warning budget ({initial_tokens} > {required_warn})")
    if expanded_tokens is not None and expanded_warn and expanded_tokens > expanded_warn:
        warnings.append(f"expanded context exceeds optional warning budget ({expanded_tokens} > {expanded_warn})")
    return ("WARN" if warnings else "PASS"), warnings


def resolve_tool_policy(defaults: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    config = defaults.get("tool_policy", {})
    profiles = config.get("profiles", {})
    profile_name = str(task.get("tool_profile") or config.get("default_profile", ""))
    profile = profiles.get(profile_name)
    if not isinstance(profile, dict):
        raise ValueError(f"unknown tool profile: {profile_name}")
    return {
        "enforcement": str(config.get("enforcement", "deny_unlisted")),
        "profile": profile_name,
        "allow": [str(item) for item in profile.get("allow", [])],
        "confirm": [str(item) for item in profile.get("confirm", [])],
        "deny": [str(item) for item in profile.get("deny", [])],
    }


def resolve_task(
    workspace_root: Path,
    task_id: str,
    bindings: dict[str, list[str]],
    include_optional: bool,
    include_template: bool,
    count_tokens: bool,
    encoding_override: str | None = None,
) -> dict[str, Any]:
    task_registry = load_yaml(workspace_root / TASK_REGISTRY_PATH)
    prompt_registry_path = str(
        task_registry.get("default_rules", {})
        .get("prompt_registry", {})
        .get("path", PROMPT_REGISTRY_PATH)
    )
    prompt_registry = load_yaml(workspace_root / prompt_registry_path)
    tasks = task_registry.get("tasks", {})
    if task_id not in tasks:
        raise KeyError(f"unknown task id: {task_id}")

    task = tasks[task_id]
    defaults = task_registry.get("default_rules", {})
    tool_policy = resolve_tool_policy(defaults, task)
    context_config = defaults.get("context_budget", {})
    resolver_config = context_config.get("resolver", {})
    token_defaults = context_config.get("token_meter", {})
    budget = merge_budget(token_defaults, task)
    encoding_name = encoding_override or str(budget.get("encoding", "o200k_base"))
    counter = TokenCounter(encoding_name)
    visible_files = git_visible_files(workspace_root)

    default_ignore = [str(item) for item in defaults.get("default_ignore", [])]
    task_ignore = [str(item) for item in task.get("ignore", [])]
    ignore_entries = default_ignore + task_ignore
    consumed_files = {
        str(item).replace("\\", "/").rstrip("/")
        for item in resolver_config.get("consumed_files", [])
    }
    retain_consumed = task_id in {
        str(item) for item in resolver_config.get("retain_consumed_for_tasks", [])
    }

    required = resolve_entries(
        workspace_root,
        [str(item) for item in task.get("required", [])],
        bindings,
        visible_files,
        ignore_entries,
        consumed_files,
        retain_consumed,
        "required",
    )
    optional = resolve_entries(
        workspace_root,
        [str(item) for item in task.get("optional", [])],
        bindings,
        visible_files,
        ignore_entries,
        consumed_files,
        retain_consumed,
        "optional",
    )
    write_scope, write_scope_unresolved = expand_text_entries(
        [str(item) for item in task.get("write_scope", [])],
        bindings,
    )
    validation, validation_unresolved = expand_text_entries(
        [str(item) for item in task.get("validation", [])],
        bindings,
    )

    preloaded_paths = [str(item) for item in resolver_config.get("preloaded_files", [])]
    preloaded = resolve_entries(
        workspace_root,
        preloaded_paths,
        {},
        visible_files,
        ignore_entries,
        set(),
        True,
        "preloaded",
    )
    preloaded_file_set = set(preloaded["files"])
    preloaded_relative = {
        path.relative_to(workspace_root.resolve()).as_posix()
        for path in preloaded_file_set
    }
    required["files"] = [
        path for path in required["files"] if path not in preloaded_file_set
    ]
    required["paths"] = [
        path
        for path in required["paths"]
        if path.replace("\\", "/").rstrip("/") not in preloaded_relative
    ]

    prompt_ids = [str(item) for item in task.get("prompt", [])]
    prompts: list[dict[str, Any]] = []
    prompt_text_parts: list[str] = []
    counted_templates: list[CountedFile] = []
    errors: list[str] = []
    max_file_bytes = int(budget.get("max_file_bytes", 2097152))
    for prompt_id in prompt_ids:
        prompt = prompt_registry.get("prompts", {}).get(prompt_id)
        if not isinstance(prompt, dict):
            errors.append(f"prompt id not found: {prompt_id}")
            continue
        frame = [str(item) for item in prompt.get("prompt_frame", [])]
        prompt_text_parts.extend(frame)
        item = {
            "id": prompt_id,
            "type": prompt.get("type"),
            "purpose": prompt.get("purpose"),
            "prompt_frame": frame,
            "template_path": prompt.get("template_path"),
        }
        template_path = prompt.get("template_path")
        if include_template and template_path:
            try:
                template_label, template_content = load_template_content(
                    workspace_root,
                    str(template_path),
                )
                template_bytes = len(template_content.encode("utf-8"))
                if template_bytes > max_file_bytes:
                    errors.append(
                        f"template exceeds max_file_bytes ({template_bytes}): {template_label}"
                    )
                else:
                    item["template_content"] = template_content
                    counted_templates.append(
                        CountedFile(
                            path=template_label,
                            bytes=template_bytes,
                            tokens=counter.count(template_content) if count_tokens else 0,
                            method=counter.method,
                            source="template",
                        )
                    )
            except (OSError, ValueError) as exc:
                errors.append(str(exc))
        prompts.append(item)

    counted_preloaded: list[CountedFile] = []
    counted_required: list[CountedFile] = []
    counted_optional: list[CountedFile] = []
    count_warnings: list[str] = []
    prompt_tokens = 0
    if count_tokens:
        counted_preloaded, warnings = count_files(
            workspace_root, preloaded["files"], counter, max_file_bytes, "preloaded"
        )
        count_warnings.extend(warnings)
        counted_required, warnings = count_files(
            workspace_root, required["files"], counter, max_file_bytes, "required"
        )
        count_warnings.extend(warnings)
        if include_optional:
            counted_optional, warnings = count_files(
                workspace_root, optional["files"], counter, max_file_bytes, "optional"
            )
            count_warnings.extend(warnings)
        prompt_tokens = counter.count("\n".join(prompt_text_parts))

    preloaded_tokens = sum(item.tokens for item in counted_preloaded)
    required_tokens = sum(item.tokens for item in counted_required)
    optional_tokens = sum(item.tokens for item in counted_optional) if include_optional else None
    template_tokens = sum(item.tokens for item in counted_templates)
    initial_tokens = preloaded_tokens + required_tokens + prompt_tokens + template_tokens
    expanded_tokens = initial_tokens + optional_tokens if optional_tokens is not None else None
    status, budget_warnings = budget_status(initial_tokens, expanded_tokens, budget)

    all_counted = counted_preloaded + counted_required + counted_optional + counted_templates
    top_count = int(budget.get("top_file_count", 10))
    largest_files = sorted(all_counted, key=lambda item: item.tokens, reverse=True)[:top_count]
    required_unresolved = set(required["unresolved"])
    optional_unresolved = set(optional["unresolved"])
    safety_unresolved = write_scope_unresolved | validation_unresolved
    active_optional_unresolved = optional_unresolved if include_optional else set()
    unresolved = sorted(
        required_unresolved | active_optional_unresolved | safety_unresolved
    )
    resource_findings = (
        required["findings"]
        + (optional["findings"] if include_optional else [])
        + preloaded["findings"]
    )
    errors.extend(
        format_resource_finding(finding)
        for finding in resource_findings
        if finding.severity == "ERROR"
    )
    errors.extend(
        f"[ERROR]\nUnresolved required placeholder:\n<{name}>\n\nAction:\npass --bind {name}=<workspace-relative-value>"
        for name in sorted(required_unresolved | safety_unresolved)
    )
    warnings = list(
        dict.fromkeys(
            [
                format_resource_finding(finding)
                for finding in resource_findings
                if finding.severity == "WARNING"
            ]
            + count_warnings
            + budget_warnings
            + (
                [
                    f"[WARNING]\nUnresolved optional placeholder:\n<{name}>\n\nImpact:\noptional context was not expanded"
                    for name in sorted(optional_unresolved)
                ]
                if include_optional
                else []
            )
        )
    )
    overall_status = "ERROR" if errors else status

    return {
        "status": overall_status,
        "task": {
            "id": task_id,
            "use_when": task.get("use_when", []),
            "use_when_zh": task.get("use_when_zh", []),
            "ledger": bool(task.get("ledger", False)),
        },
        "workspace_root": str(workspace_root),
        "bindings": bindings,
        "context": {
            "preloaded_paths": preloaded["paths"],
            "required_paths": required["paths"],
            "optional_paths": optional["paths"],
            "external_evidence": required["evidence"],
            "optional_evidence": optional["evidence"],
            "ignored": task_ignore,
            "write_scope": write_scope,
            "validation": validation,
            "resolver_consumed_files": required["consumed"],
            "resolver_internal_reads": [
                TASK_REGISTRY_PATH,
                prompt_registry_path,
            ],
            "unresolved_placeholders": unresolved,
            "resource_findings": [
                finding.__dict__ for finding in resource_findings
            ],
        },
        "prompts": prompts,
        "tool_policy": tool_policy,
        "token_budget": {
            "enabled": count_tokens,
            "encoding": encoding_name,
            "method": counter.method,
            "exact": counter.exact,
            "enforcement": budget.get("enforcement", "warn"),
            "required_warn_tokens": budget.get("required_warn_tokens"),
            "expanded_warn_tokens": budget.get("expanded_warn_tokens"),
            "hard_max_tokens": budget.get("hard_max_tokens"),
            "preloaded_tokens": preloaded_tokens,
            "required_file_tokens": required_tokens,
            "prompt_frame_tokens": prompt_tokens,
            "template_tokens": template_tokens,
            "optional_tokens": optional_tokens,
            "initial_tokens": initial_tokens,
            "expanded_tokens": expanded_tokens,
            "optional_measured": include_optional,
            "budget_status": status,
            "status": overall_status,
            "largest_files": [item.__dict__ for item in largest_files],
        },
        "warnings": warnings,
        "errors": errors,
    }


def resolve_prompt(
    workspace_root: Path,
    prompt_id: str,
    include_template: bool,
    count_tokens: bool,
    encoding_override: str | None = None,
) -> dict[str, Any]:
    task_registry = load_yaml(workspace_root / TASK_REGISTRY_PATH)
    prompt_registry_path = str(
        task_registry.get("default_rules", {})
        .get("prompt_registry", {})
        .get("path", PROMPT_REGISTRY_PATH)
    )
    prompt_registry = load_yaml(workspace_root / prompt_registry_path)
    prompt = prompt_registry.get("prompts", {}).get(prompt_id)
    if not isinstance(prompt, dict):
        raise KeyError(f"unknown prompt id: {prompt_id}")

    budget = (
        task_registry.get("default_rules", {})
        .get("context_budget", {})
        .get("token_meter", {})
    )
    encoding_name = encoding_override or str(budget.get("encoding", "o200k_base"))
    counter = TokenCounter(encoding_name)
    frame = [str(item) for item in prompt.get("prompt_frame", [])]
    frame_text = "\n".join(frame)
    template_reference = prompt.get("template_path")
    template_label = None
    template_content = None
    template_tokens = 0
    errors: list[str] = []
    if include_template and template_reference:
        try:
            template_label, template_content = load_template_content(
                workspace_root,
                str(template_reference),
            )
            max_file_bytes = int(budget.get("max_file_bytes", 2097152))
            template_bytes = len(template_content.encode("utf-8"))
            if template_bytes > max_file_bytes:
                errors.append(
                    f"template exceeds max_file_bytes ({template_bytes}): {template_label}"
                )
                template_content = None
            elif count_tokens:
                template_tokens = counter.count(template_content)
        except (OSError, ValueError) as exc:
            errors.append(str(exc))

    return {
        "mode": "prompt",
        "workspace_root": str(workspace_root),
        "prompt": {
            "id": prompt_id,
            "type": prompt.get("type"),
            "purpose": prompt.get("purpose"),
            "platform": prompt.get("platform"),
            "exposures": prompt.get("exposures", []),
            "prompt_frame": frame,
            "template_path": template_reference,
            "resolved_template": template_label,
            "template_content": template_content,
        },
        "token_budget": {
            "enabled": count_tokens,
            "encoding": encoding_name,
            "method": counter.method,
            "exact": counter.exact,
            "prompt_frame_tokens": counter.count(frame_text) if count_tokens else 0,
            "template_tokens": template_tokens,
            "total_tokens": (counter.count(frame_text) if count_tokens else 0)
            + template_tokens,
        },
        "errors": errors,
    }


def print_task_list(task_registry: dict[str, Any], output_format: str) -> None:
    rows_by_id = {
        task_id: {
            "id": task_id,
            "use_when": task.get("use_when", []),
            "use_when_zh": task.get("use_when_zh", []),
        }
        for task_id, task in task_registry.get("tasks", {}).items()
    }
    rows = [
        {
            "id": task_id,
            "use_when": task.get("use_when", []),
            "use_when_zh": task.get("use_when_zh", []),
        }
        for task_id, task in task_registry.get("tasks", {}).items()
    ]
    if output_format == "json":
        print(json.dumps({"tasks": rows}, ensure_ascii=False, indent=2))
        return

    printed: set[str] = set()
    print("Registered workspace tasks")
    print("Use `workspace task resolve <task-id>` to inspect context, write scope, and validation.")
    for group_name, task_ids in TASK_GROUPS:
        group_rows = [rows_by_id[task_id] for task_id in task_ids if task_id in rows_by_id]
        if not group_rows:
            continue
        print("")
        print(group_name)
        print_task_table(group_rows)
        printed.update(row["id"] for row in group_rows)
    remaining = [row for row in rows if row["id"] not in printed]
    if remaining:
        print("")
        print("Other")
        print_task_table(remaining)


def print_task_table(rows: list[dict[str, Any]]) -> None:
    id_width = 34
    desc_width = 76
    print(f"{'Task id':<{id_width}}  Use when")
    print(f"{'-' * id_width}  {'-' * 24}")
    for row in rows:
        description = row["use_when"][0] if row["use_when"] else ""
        if row["use_when_zh"]:
            description = f"{description} / {row['use_when_zh'][0]}"
        wrapped = textwrap.wrap(
            description,
            width=desc_width,
            break_long_words=False,
            break_on_hyphens=False,
        ) or [""]
        print(f"{row['id']:<{id_width}}  {wrapped[0]}")
        for line in wrapped[1:]:
            print(f"{'':<{id_width}}  {line}")


def print_prompt_list(prompt_registry: dict[str, Any], output_format: str) -> None:
    rows = [
        {
            "id": prompt_id,
            "type": prompt.get("type"),
            "purpose": prompt.get("purpose"),
            "template_path": prompt.get("template_path"),
        }
        for prompt_id, prompt in prompt_registry.get("prompts", {}).items()
    ]
    if output_format == "json":
        print(json.dumps({"prompts": rows}, ensure_ascii=False, indent=2))
        return
    for row in rows:
        suffix = f" -> {row['template_path']}" if row.get("template_path") else ""
        print(f"{row['id']} [{row.get('type', '')}]: {row.get('purpose', '')}{suffix}")


def print_prompt_text(result: dict[str, Any]) -> None:
    prompt = result["prompt"]
    budget = result["token_budget"]
    print(f"Prompt: {prompt['id']}")
    print(f"Purpose: {prompt.get('purpose', '')}")
    if prompt.get("platform"):
        print(f"Default exposure: {prompt['platform']}")
    if prompt.get("exposures"):
        print(f"Exposures: {', '.join(prompt['exposures'])}")
    if prompt.get("template_path"):
        print(f"Template: {prompt['template_path']}")
    if prompt.get("prompt_frame"):
        print("")
        print("Prompt frame:")
        for line in prompt["prompt_frame"]:
            print(f"- {line}")
    if prompt.get("template_content") is not None:
        print("")
        print("Resolved template:")
        print(prompt["template_content"].rstrip())
    print("")
    print("Token estimate:")
    print(f"- Method: {budget['method']}")
    print(f"- Prompt frame: {budget['prompt_frame_tokens']}")
    print(f"- Template: {budget['template_tokens']}")
    print(f"- Total: {budget['total_tokens']}")
    if result["errors"]:
        print("")
        print("Errors:")
        for error in result["errors"]:
            print(f"- {error}")


def print_text(result: dict[str, Any]) -> None:
    task = result["task"]
    context = result["context"]
    budget = result["token_budget"]
    print(f"Task: {task['id']}")
    print(f"Workspace: {result['workspace_root']}")
    print("")
    print("Required context:")
    for path in context["required_paths"]:
        print(f"- {path}")
    if not context["required_paths"]:
        print("- None.")
    if context["resolver_consumed_files"]:
        print("")
        print("Resolved internally; do not reread by default:")
        for path in context["resolver_consumed_files"]:
            print(f"- {path}")
    if context["external_evidence"]:
        print("")
        print("External evidence or commands:")
        for item in context["external_evidence"]:
            print(f"- {item}")
    print("")
    print("Prompt guidance:")
    for prompt in result["prompts"]:
        print(f"- {prompt['id']}: {prompt.get('purpose', '')}")
        for line in prompt.get("prompt_frame", []):
            print(f"  - {line}")
    tool_policy = result["tool_policy"]
    print("")
    print(f"Tool policy: {tool_policy['profile']} ({tool_policy['enforcement']})")
    print(f"- Allow: {', '.join(tool_policy['allow']) or 'None'}")
    print(f"- Confirm: {', '.join(tool_policy['confirm']) or 'None'}")
    print(f"- Deny: {', '.join(tool_policy['deny']) or 'None'}")
    print("")
    print("Token budget:")
    print(f"- Method: {budget['method']}")
    print(f"- Preloaded: {budget['preloaded_tokens']}")
    print(f"- Required files: {budget['required_file_tokens']}")
    print(f"- Prompt frame: {budget['prompt_frame_tokens']}")
    print(f"- Initial total: {budget['initial_tokens']} / {budget['required_warn_tokens']}")
    if budget["optional_measured"]:
        print(f"- Optional: {budget['optional_tokens']}")
        print(f"- Expanded total: {budget['expanded_tokens']} / {budget['expanded_warn_tokens']}")
    else:
        print("- Optional: not measured; pass --include-optional to expand")
    print(f"- Status: {budget['status']}")
    if context["unresolved_placeholders"]:
        print("")
        print("Unresolved placeholders:")
        for name in context["unresolved_placeholders"]:
            print(f"- <{name}>")
    if result["warnings"]:
        print("")
        print("Warnings:")
        for warning in result["warnings"]:
            print(f"- {warning}")
    if result["errors"]:
        print("")
        print("Errors:")
        for error in result["errors"]:
            print(f"- {error}")


ROUTING_EVENTS_PATH = os.path.normpath(
    os.environ.get(
        "AI_TOOL_STAGING_DIR",
        # Cross-platform fallback: relative to this script's directory
        os.path.join(os.path.dirname(__file__), "..", ".claude"),
    )
) + os.sep + "routing_events.ndjson"


def record_routing_event(result: dict[str, Any]) -> None:
    """Append a routing-resolution event to the NDJSON log."""
    task = result.get("task", {})
    ctx = result.get("context", {})
    budget = result.get("token_budget", {})

    # Derive the "files_requested" count from context paths
    files_requested = len(ctx.get("required_paths", []))
    if budget.get("optional_measured"):
        files_requested += len(ctx.get("optional_paths", []))

    intent_en = (task.get("use_when") or [None])[0] or ""
    intent_zh = (task.get("use_when_zh") or [None])[0] or ""

    event = {
        "event_type": "resolution",
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "task_id": task.get("id", ""),
        "intent_en": intent_en,
        "intent_zh": intent_zh,
        "n_preloaded": len(ctx.get("preloaded_paths", [])),
        "n_required": len(ctx.get("required_paths", [])),
        "n_optional": len(ctx.get("optional_paths", [])),
        "n_optional_measured": budget.get("optional_measured", False),
        "tokens_preloaded": budget.get("preloaded_tokens", 0),
        "tokens_required": budget.get("required_file_tokens", 0),
        "tokens_optional": budget.get("optional_tokens", 0),
        "tokens_prompt": budget.get("prompt_frame_tokens", 0),
        "tokens_total_initial": budget.get("initial_tokens", 0),
        "tokens_total_expanded": budget.get("expanded_tokens", 0),
        "budget_status": budget.get("status", ""),
        "budget_enforcement": budget.get("enforcement", ""),
        "has_resource_errors": bool(result.get("errors")),
        "has_resource_warnings": bool(result.get("warnings")),
        "encoding": budget.get("encoding", ""),
    }

    try:
        dir_path = os.path.dirname(ROUTING_EVENTS_PATH)
        os.makedirs(dir_path, exist_ok=True)
        with open(ROUTING_EVENTS_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        pass  # best-effort recording


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve a registered task into minimal context and token estimates."
    )
    parser.add_argument("task", nargs="?", help="Exact task id from PROJECT_CONTEXT/task_registry.yaml.")
    parser.add_argument("--list", action="store_true", help="List registered task ids.")
    parser.add_argument("--list-prompts", action="store_true", help="List registered prompt ids.")
    parser.add_argument("--prompt-id", help="Resolve one prompt id directly.")
    parser.add_argument("--start", default=".", help="Workspace path or child path.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--bind", action="append", default=[], metavar="NAME=VALUE")
    parser.add_argument("--include-optional", action="store_true")
    parser.add_argument("--include-template", action="store_true")
    parser.add_argument("--no-token-count", action="store_true")
    parser.add_argument("--strict-budget", action="store_true")
    parser.add_argument("--encoding", help="Override token encoding, for example o200k_base.")
    args = parser.parse_args()

    manifest_path = find_manifest(
        Path(args.start),
        DEFAULT_MANIFEST_FILENAME,
        DEFAULT_MAX_PARENT_DEPTH,
    )
    if manifest_path is None:
        print("[ERROR] workspace_manifest.yaml was not found by bounded parent lookup.", file=sys.stderr)
        return 1
    workspace_root = manifest_path.parent.resolve()

    try:
        task_registry = load_yaml(workspace_root / TASK_REGISTRY_PATH)
        if args.list:
            print_task_list(task_registry, args.format)
            return 0
        if args.list_prompts:
            prompt_registry_path = str(
                task_registry.get("default_rules", {})
                .get("prompt_registry", {})
                .get("path", PROMPT_REGISTRY_PATH)
            )
            print_prompt_list(load_yaml(workspace_root / prompt_registry_path), args.format)
            return 0
        if args.prompt_id:
            if args.task:
                parser.error("task id and --prompt-id are mutually exclusive")
            result = resolve_prompt(
                workspace_root=workspace_root,
                prompt_id=args.prompt_id,
                include_template=args.include_template,
                count_tokens=not args.no_token_count,
                encoding_override=args.encoding,
            )
            if args.format == "json":
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print_prompt_text(result)
            return 1 if result["errors"] else 0
        if not args.task:
            parser.error(
                "task id is required unless --list, --list-prompts, or --prompt-id is used"
            )
        bindings = parse_bindings(args.bind)
        result = resolve_task(
            workspace_root=workspace_root,
            task_id=args.task,
            bindings=bindings,
            include_optional=args.include_optional,
            include_template=args.include_template,
            count_tokens=not args.no_token_count,
            encoding_override=args.encoding,
        )
    except (KeyError, OSError, ValueError, RuntimeError) as exc:
        if args.format == "json":
            print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
        else:
            print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    record_routing_event(result)

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_text(result)

    if result["errors"]:
        return 1
    if args.strict_budget and result["token_budget"]["status"] != "PASS":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
