from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml


from scripts.workspace.runtime import WORKSPACE_ROOT
REGISTRY_PATH = WORKSPACE_ROOT / "PROJECT_CONTEXT" / "knowledge_registry.yaml"
TOKEN_PATTERN = re.compile(r"[a-z0-9_-]+|[\u3400-\u9fff]+", re.IGNORECASE)
LAYER_ALIASES = {"skill_engineering": "workspace_engineering"}


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict) or not isinstance(payload.get("topics"), dict):
        raise ValueError("knowledge registry must contain a topics mapping")
    return payload


def normalize(value: str) -> str:
    return " ".join(value.lower().strip().split())


def tokens(value: str) -> set[str]:
    return {token.lower() for token in TOKEN_PATTERN.findall(value)}


def topic_score(topic_id: str, topic: dict[str, Any], query: str) -> tuple[int, list[str]]:
    normalized_query = normalize(query)
    query_tokens = tokens(query)
    title = normalize(str(topic.get("title", "")))
    aliases = [normalize(str(alias)) for alias in topic.get("aliases", [])]
    topic_name = normalize(topic_id.replace("_", " "))
    reasons: list[str] = []
    score = 0

    if normalized_query in {topic_name, normalize(topic_id)}:
        score = 120
        reasons.append("exact topic id")
    if normalized_query == title:
        score = max(score, 110)
        reasons.append("exact title")
    if normalized_query in aliases:
        score = max(score, 100)
        reasons.append("exact alias")

    searchable = [topic_name, title, *aliases]
    substring_matches = [value for value in searchable if normalized_query and normalized_query in value]
    if substring_matches:
        score = max(score, 75)
        reasons.append("query phrase appears in topic metadata")

    overlap = max((len(query_tokens & tokens(value)) for value in searchable), default=0)
    if overlap:
        score = max(score, overlap * 20)
        reasons.append(f"{overlap} keyword token(s) matched")
    return score, reasons


def validate_entries(topic: dict[str, Any], layer: str | None) -> tuple[list[dict[str, Any]], list[str]]:
    layer = LAYER_ALIASES.get(layer, layer)
    entries: list[dict[str, Any]] = []
    warnings: list[str] = []
    for entry in topic.get("entries", []):
        if layer and entry.get("layer") != layer:
            continue
        path = str(entry.get("path", ""))
        exists = (WORKSPACE_ROOT / path).exists()
        if not exists:
            warnings.append(f"missing indexed path: {path}")
        entries.append({**entry, "exists": exists})
    return entries, warnings


def find_topics(
    registry: dict[str, Any],
    query: str,
    limit: int,
    layer: str | None,
) -> dict[str, Any]:
    layer = LAYER_ALIASES.get(layer, layer)
    matches: list[dict[str, Any]] = []
    warnings: list[str] = []
    for topic_id, topic in registry["topics"].items():
        score, reasons = topic_score(topic_id, topic, query)
        if score <= 0:
            continue
        entries, entry_warnings = validate_entries(topic, layer)
        warnings.extend(entry_warnings)
        if layer and not entries:
            continue
        matches.append(
            {
                "topic_id": topic_id,
                "title": topic.get("title"),
                "score": score,
                "match_reasons": reasons,
                "entries": entries,
            }
        )
    matches.sort(key=lambda match: (-match["score"], match["topic_id"]))
    if matches:
        minimum_score = max(20, matches[0]["score"] - 60)
        matches = [match for match in matches if match["score"] >= minimum_score]
    return {
        "status": "PASS" if matches else "NO_MATCH",
        "query": query,
        "layer": layer,
        "matches": matches[:limit],
        "warnings": sorted(set(warnings)),
        "guidance": (
            "Read only the returned entry files needed for the task. "
            "The registry routes knowledge but does not replace source authority."
        ),
    }


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
        entries, entry_warnings = validate_entries(topic, None)
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

    print(f"Status: {payload['status']}")
    print(f"Query: {payload['query']}")
    for match in payload["matches"]:
        print(f"\n{match['topic_id']}: {match['title']} (score {match['score']})")
        for entry in match["entries"]:
            marker = "OK" if entry["exists"] else "MISSING"
            print(f"  - {entry['path']} [{entry['layer']}, {marker}]")
            print(f"    {entry['purpose']}")
    for warning in payload["warnings"]:
        print(f"\nWARNING: {warning}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Find bounded workspace knowledge entry points without scanning files."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list", action="store_true", help="List registered knowledge topics.")
    mode.add_argument("--validate", action="store_true", help="Check every indexed path.")
    mode.add_argument("--query", help="Topic, phrase, or alias to find.")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument(
        "--layer",
        choices=(
            "project_context",
            "shared",
            "workspace_engineering",
            "skill_engineering",
            "usage_guides",
            "manifest",
            "tooling",
            "documentation",
        ),
    )
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
        else:
            payload = find_topics(registry, args.query, max(1, args.limit), args.layer)
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
