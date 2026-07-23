"""Canonical PROJECT_CONTEXT paths and split-registry loaders."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from scripts.workspace.runtime import WORKSPACE_ROOT


PROJECT_CONTEXT_ROOT = WORKSPACE_ROOT / "PROJECT_CONTEXT"
CONTEXT_INDEX_PATH = PROJECT_CONTEXT_ROOT / "context_index.yaml"
TASKS_ROOT = PROJECT_CONTEXT_ROOT / "tasks"
TASK_REGISTRY_ROOT = TASKS_ROOT / "registry"
TASK_REGISTRY_INDEX_PATH = TASK_REGISTRY_ROOT / "index.yaml"
KNOWLEDGE_ROOT = PROJECT_CONTEXT_ROOT / "knowledge"
KNOWLEDGE_INDEX_PATH = KNOWLEDGE_ROOT / "index.yaml"
DOC_REGISTRY_PATH = PROJECT_CONTEXT_ROOT / "documentation" / "doc_pair_registry.yaml"
TASK_LEDGER_ROOT = TASKS_ROOT / "ledger"
TASK_RECORDS_ROOT = TASKS_ROOT / "records"


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a YAML mapping in {path}")
    return payload


def load_context_index(root: Path = PROJECT_CONTEXT_ROOT) -> dict[str, Any]:
    path = root / "context_index.yaml"
    return load_yaml(path)


def _load_split_collection(
    index_path: Path,
    collection_key: str,
    file_map_key: str,
) -> dict[str, Any]:
    if not index_path.is_file():
        raise FileNotFoundError(f"Missing canonical registry index: {index_path}")
    index = load_yaml(index_path)
    file_map = index.get(file_map_key)
    if not isinstance(file_map, dict):
        return index
    merged = {
        key: value
        for key, value in index.items()
        if key not in {file_map_key, collection_key}
    }
    collection: dict[str, Any] = {}
    for item_id, relative_path in file_map.items():
        if not isinstance(item_id, str) or not isinstance(relative_path, str):
            raise ValueError(f"Invalid {file_map_key} entry in {index_path}")
        if Path(relative_path).is_absolute():
            raise ValueError(f"Absolute {file_map_key} path is not allowed: {relative_path}")
        base = index_path.parent.resolve()
        path = (base / relative_path).resolve()
        try:
            path.relative_to(base)
        except ValueError as error:
            raise ValueError(f"{file_map_key} path escapes canonical root: {relative_path}") from error
        if not path.is_file():
            raise FileNotFoundError(f"Missing {file_map_key} target: {path}")
        payload = load_yaml(path)
        grouped = payload.get(collection_key)
        if not isinstance(grouped, dict) or not grouped:
            raise ValueError(f"{path} must define a non-empty {collection_key} mapping")
        collection.update(grouped)
    merged[collection_key] = collection
    return merged


def load_task_registry(root: Path = PROJECT_CONTEXT_ROOT) -> dict[str, Any]:
    canonical = root / "tasks" / "registry" / "index.yaml"
    return _load_split_collection(canonical, "tasks", "task_files")


def load_knowledge_registry(root: Path = PROJECT_CONTEXT_ROOT) -> dict[str, Any]:
    canonical = root / "knowledge" / "index.yaml"
    return _load_split_collection(canonical, "topics", "topic_files")


def load_doc_pair_registry(root: Path = PROJECT_CONTEXT_ROOT) -> dict[str, Any]:
    return load_yaml(root / "documentation" / "doc_pair_registry.yaml")
