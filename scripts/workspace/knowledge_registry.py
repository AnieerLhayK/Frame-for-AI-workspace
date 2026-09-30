from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from scripts.workspace.project_context import KNOWLEDGE_INDEX_PATH, load_knowledge_registry
from scripts.workspace.runtime import WORKSPACE_ROOT

REGISTRY_PATH = KNOWLEDGE_INDEX_PATH


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    if path == REGISTRY_PATH:
        return load_knowledge_registry()
    payload = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict) or not isinstance(payload.get("topics"), dict):
        raise ValueError("knowledge registry must contain a topics mapping")
    return payload


def validate_entries(topic: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    entries: list[dict[str, Any]] = []
    warnings: list[str] = []
    for entry in topic.get("entries", []):
        path = str(entry.get("path", ""))
        exists = (WORKSPACE_ROOT / path).exists()
        if not exists:
            warnings.append(f"missing indexed path: {path}")
        entries.append({**entry, "exists": exists})
    return entries, warnings


def list_topics(registry: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "PASS",
        "topics": [
            {
                "topic_id": topic_id,
                "title": topic.get("title"),
                "aliases": topic.get("aliases", []),
            }
            for topic_id, topic in registry["topics"].items()
        ],
    }


def validate_registry(registry: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = []
    entry_count = 0
    for topic in registry["topics"].values():
        entries, entry_warnings = validate_entries(topic)
        entry_count += len(entries)
        warnings.extend(entry_warnings)
    return {
        "status": "PASS" if not warnings else "ERROR",
        "topic_count": len(registry["topics"]),
        "entry_count": entry_count,
        "warnings": sorted(set(warnings)),
    }


def render_text(payload: dict[str, Any]) -> None:
    if "topic_count" in payload:
        print(f"Status: {payload['status']}")
        print(f"Topics: {payload['topic_count']}")
        print(f"Entries: {payload['entry_count']}")
        for warning in payload["warnings"]:
            print(f"WARNING: {warning}")
        return
    if "topics" in payload:
        for topic in payload["topics"]:
            print(f"{topic['topic_id']}: {topic['title']}")
        return


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List and validate the bounded workspace knowledge registry."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list", action="store_true", help="List registered knowledge topics.")
    mode.add_argument("--validate", action="store_true", help="Check every indexed path.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        registry = load_registry()
        if args.list:
            payload = list_topics(registry)
        elif args.validate:
            payload = validate_registry(registry)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        payload = {"status": "ERROR", "error": str(exc)}
        print(json.dumps(payload, indent=2) if args.format == "json" else f"ERROR: {exc}")
        return 1

    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        render_text(payload)
    return 0 if payload["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
