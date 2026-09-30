"""Validate the canonical-only PROJECT_CONTEXT layout."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from scripts.workspace.project_context import (
    PROJECT_CONTEXT_ROOT,
    TASK_LEDGER_ROOT,
    TASK_RECORDS_ROOT,
    load_context_index,
    load_doc_pair_registry,
    load_knowledge_registry,
    load_task_registry,
)
from scripts.workspace.runtime import WORKSPACE_ROOT


@dataclass(frozen=True)
class Finding:
    level: str
    message: str


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _file_map_findings(index_path: Path, key: str, collection_key: str, display_name: str) -> list[Finding]:
    findings: list[Finding] = []
    import yaml

    index = yaml.safe_load(index_path.read_text(encoding="utf-8-sig")) or {}
    file_map = index.get(key)
    if not isinstance(file_map, dict) or not file_map:
        return [Finding("ERROR", f"{_display_path(index_path, WORKSPACE_ROOT)} missing {key}")]
    for item_id, relative in file_map.items():
        if not isinstance(item_id, str) or not isinstance(relative, str):
            findings.append(Finding("ERROR", f"invalid {key} entry in {index_path.name}"))
            continue
        if Path(relative).is_absolute():
            findings.append(Finding("ERROR", f"absolute {key} path: {relative}"))
            continue
        base = index_path.parent.resolve()
        target = (base / relative).resolve()
        try:
            target.relative_to(base)
        except ValueError:
            findings.append(Finding("ERROR", f"{key} path escapes canonical root: {relative}"))
            continue
        if not target.is_file():
            findings.append(Finding("ERROR", f"missing {display_name} source: {_display_path(target, WORKSPACE_ROOT)}"))
            continue
        try:
            payload = yaml.safe_load(target.read_text(encoding="utf-8-sig")) or {}
        except (OSError, yaml.YAMLError) as error:
            findings.append(Finding("ERROR", f"cannot load {display_name} source {target}: {error}"))
            continue
        grouped = payload.get(collection_key)
        if not isinstance(grouped, dict) or not grouped:
            findings.append(Finding("ERROR", f"{_display_path(target, WORKSPACE_ROOT)} must define a non-empty {collection_key} mapping"))
    return findings


def validate(root: Path = PROJECT_CONTEXT_ROOT) -> list[Finding]:
    findings: list[Finding] = []
    required = [
        root / "README.md",
        root / "README.zh-CN.md",
        root / "context_index.yaml",
        root / "tasks" / "README.md",
        root / "tasks" / "registry" / "README.md",
        root / "knowledge" / "README.md",
        root / "documentation" / "README.md",
        root / "continuity" / "README.md",
        root / "governance" / "README.md",
        root / "memory" / "README.md",
        root / "references" / "README.md",
    ]
    for path in required:
        if not path.is_file():
            findings.append(Finding("ERROR", f"missing required PROJECT_CONTEXT path: {_display_path(path, root)}"))

    try:
        context = load_context_index(root)
        if context.get("schema_version") != "0.1":
            findings.append(Finding("ERROR", "context_index.yaml must use schema 0.1"))
        aliases = context.get("legacy_paths")
        if aliases is not None and not isinstance(aliases, dict):
            findings.append(Finding("ERROR", "context_index legacy_paths must be a mapping when present"))
    except (OSError, ValueError) as error:
        findings.append(Finding("ERROR", f"cannot load context index: {error}"))

    try:
        task_registry = load_task_registry(root)
        if task_registry.get("schema_version") != "0.2":
            findings.append(Finding("ERROR", "task registry index must use schema 0.2"))
        if not isinstance(task_registry.get("tasks"), dict) or not task_registry["tasks"]:
            findings.append(Finding("ERROR", "task registry has no loaded tasks"))
        findings.extend(_file_map_findings(root / "tasks" / "registry" / "index.yaml", "task_files", "tasks", "task domain"))
    except (OSError, ValueError) as error:
        findings.append(Finding("ERROR", f"cannot load task registry: {error}"))

    try:
        knowledge = load_knowledge_registry(root)
        if knowledge.get("schema_version") != "0.2":
            findings.append(Finding("ERROR", "knowledge index must use schema 0.2"))
        if not isinstance(knowledge.get("topics"), dict) or not knowledge["topics"]:
            findings.append(Finding("ERROR", "knowledge index has no loaded topics"))
        findings.extend(_file_map_findings(root / "knowledge" / "index.yaml", "topic_files", "topics", "knowledge topic"))
    except (OSError, ValueError) as error:
        findings.append(Finding("ERROR", f"cannot load knowledge registry: {error}"))

    try:
        load_doc_pair_registry(root)
        if not (root / "documentation" / "doc_pair_registry.yaml").is_file():
            findings.append(Finding("ERROR", "canonical doc pair registry is missing"))
    except (OSError, ValueError) as error:
        findings.append(Finding("ERROR", f"cannot load doc pair registry: {error}"))

    if not TASK_LEDGER_ROOT.is_dir():
        findings.append(Finding("ERROR", "canonical task ledger directory is missing"))
    if not TASK_RECORDS_ROOT.is_dir():
        findings.append(Finding("ERROR", "canonical task records directory is missing"))
    for legacy_dir in (root / "task_ledger", root / "task_records"):
        if legacy_dir.exists():
            findings.append(Finding("ERROR", f"legacy task fact directory remains: {_display_path(legacy_dir, root)}"))
    for legacy_file in (
        root / "task_registry.yaml",
        root / "knowledge_registry.yaml",
        root / "doc_pair_registry.yaml",
    ):
        if legacy_file.exists():
            findings.append(Finding("ERROR", f"retired compatibility projection remains: {_display_path(legacy_file, root)}"))
    return findings


def main() -> int:
    findings = validate()
    for finding in findings:
        print(f"{finding.level}: {finding.message}")
    if findings:
        return 1
    print("PROJECT_CONTEXT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
