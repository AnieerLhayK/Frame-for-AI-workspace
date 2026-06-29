from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = WORKSPACE_ROOT / "workspace_manifest.yaml"
TASK_REGISTRY_PATH = WORKSPACE_ROOT / "PROJECT_CONTEXT" / "task_registry.yaml"
KNOWLEDGE_REGISTRY_PATH = WORKSPACE_ROOT / "PROJECT_CONTEXT" / "knowledge_registry.yaml"

MECHANISMS: dict[str, dict[str, Any]] = {
    "task-routing": {
        "title": "Task routing and context budget",
        "purpose": "Map a maintenance request to required context, write scope, validation, and token budget.",
        "entrypoints": [
            "workspace task list",
            "workspace task resolve <task-id>",
            "workspace preflight <task-id>",
        ],
        "sources": [
            "PROJECT_CONTEXT/task_registry.yaml",
            "PROJECT_CONTEXT/context_budget.md",
            "USAGE_GUIDES/prompt_registry.yaml",
            "scripts/resolve_task_context.py",
        ],
        "checks": [
            "python -m unittest scripts.tests.test_resolve_task_context",
            "workspace workflow check <task-id>",
        ],
    },
    "model-routing": {
        "title": "Claude model recommendation policy",
        "purpose": "Tell Claude Code when to visibly recommend deepseek-v4-pro without changing model configuration or authority.",
        "entrypoints": ["CLAUDE.md", "workspace health"],
        "sources": [
            "shared/claude/policies/model-routing-policy.md",
            "scripts/workspace_health.py",
            "scripts/tests/test_workspace_health.py",
        ],
        "checks": ["python -m unittest scripts.tests.test_workspace_health"],
    },
    "report-freshness": {
        "title": "Snapshot report freshness",
        "purpose": "Detect stale generated reports and refresh them explicitly from source evidence.",
        "entrypoints": ["workspace reports status", "workspace reports refresh all-current"],
        "sources": [
            "shared/reporting_policy.md",
            "scripts/report_status.py",
            "reports/",
        ],
        "checks": [
            "workspace reports status --strict",
            "python -m unittest scripts.tests.test_report_status",
        ],
    },
    "platform-exposure": {
        "title": "Platform skill exposure",
        "purpose": "Keep platform loading surfaces as projections of manifest-declared source skills.",
        "entrypoints": ["workspace skill list", "workspace skill expose <skill-id> --platform <platform>"],
        "sources": [
            "workspace_manifest.yaml",
            "shared/workspace_path_policy.md",
            "scripts/skill_lifecycle.py",
        ],
        "checks": ["workspace validate links", "workspace skill validate <skill-id>"],
    },
    "agent-governance": {
        "title": "Agent authority and runtime guards",
        "purpose": "Resolve agent roles and guard structural writes across Codex, Claude, Hermes, OpenCode, and related hosts.",
        "entrypoints": ["workspace agent status", "workspace agent check --agent <id> --path <path>"],
        "sources": [
            "shared/agent_registry.yaml",
            "shared/agent_governance.yaml",
            "shared/agent_governance_policy.md",
            "scripts/agent_governance.py",
        ],
        "checks": ["workspace health --with-tests", "workspace agent doctor hermes"],
    },
    "runtime-drift": {
        "title": "Character runtime drift loop",
        "purpose": "Route runtime style drift through diagnosis, maintenance, validation, and optional generalization.",
        "entrypoints": ["style-doctor", "character-maintainer"],
        "sources": [
            "packages/character-system/shared/runtime_loop_policy.md",
            "packages/character-system/reports/runtime-loop/",
            "WORKSPACE_ENGINEERING/skill_engineering/runtime_loop_patterns.md",
        ],
        "checks": ["workspace knowledge find \"runtime drift\""],
    },
}


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else {}


def normalize_path(value: str) -> str:
    return value.replace("\\", "/").strip("/")


def path_matches(entry: str, target: str) -> bool:
    entry = normalize_path(entry)
    target = normalize_path(target)
    if not entry or entry.startswith(("actual ", "explicit ", "all task ", "relevant ")):
        return False
    if entry.endswith("/"):
        return target.startswith(entry)
    return entry == target or target.startswith(entry.rstrip("/") + "/")


def infer_layer(path: str) -> str:
    normalized = normalize_path(path)
    if normalized == "workspace_manifest.yaml":
        return "manifest"
    top = normalized.split("/", 1)[0]
    return {
        "PROJECT_CONTEXT": "project context",
        "shared": "workspace policy",
        "packages": "package/domain source",
        "skills": "standalone skill source",
        "scripts": "tooling",
        "USAGE_GUIDES": "usage guide",
        "WORKSPACE_ENGINEERING": "reusable methodology",
        "reports": "generated report snapshot",
        ".claude": "Claude Code project boundary",
    }.get(top, "workspace root")


def manifest_matches(path: str, manifest: dict[str, Any]) -> list[str]:
    matches: list[str] = []
    for section in ("skills", "projections", "protocols", "packages"):
        for item in manifest.get(section, []) or []:
            if not isinstance(item, dict):
                continue
            label = item.get("id") or item.get("name") or item.get("package_id") or section
            for key, value in item.items():
                if isinstance(value, str) and path_matches(value, path):
                    matches.append(f"{section}: {label} via {key}={value}")
    return matches


def task_matches(path: str, registry: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for task_id, task in (registry.get("tasks") or {}).items():
        if not isinstance(task, dict):
            continue
        reasons = []
        for field in ("required", "optional", "write_scope", "validation"):
            values = task.get(field, []) or []
            if any(isinstance(value, str) and path_matches(value, path) for value in values):
                reasons.append(field)
        if reasons:
            rows.append(
                {
                    "id": task_id,
                    "reason": ", ".join(reasons),
                    "summary": (task.get("use_when") or [""])[0],
                }
            )
    return rows


def knowledge_matches(path: str, registry: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for topic_id, topic in (registry.get("topics") or {}).items():
        for entry in topic.get("entries", []) or []:
            if isinstance(entry, dict) and path_matches(str(entry.get("path", "")), path):
                rows.append(
                    {
                        "topic": topic_id,
                        "title": str(topic.get("title", "")),
                        "purpose": str(entry.get("purpose", "")),
                    }
                )
    return rows


def test_candidates(path: str) -> list[str]:
    normalized = normalize_path(path)
    candidates: list[str] = []
    if normalized.startswith("scripts/") and normalized.endswith(".py"):
        stem = Path(normalized).stem
        candidates.append(f"scripts/tests/test_{stem}.py")
    if normalized.startswith("scripts/tests/"):
        candidates.append(normalized)
    return [candidate for candidate in candidates if (WORKSPACE_ROOT / candidate).is_file()]


def explain_path(path: str) -> dict[str, Any]:
    normalized = normalize_path(path)
    manifest = load_yaml(MANIFEST_PATH)
    tasks = load_yaml(TASK_REGISTRY_PATH)
    knowledge = load_yaml(KNOWLEDGE_REGISTRY_PATH)
    exists = (WORKSPACE_ROOT / normalized).exists()
    return {
        "mode": "path",
        "path": normalized,
        "exists": exists,
        "layer": infer_layer(normalized),
        "manifest_matches": manifest_matches(normalized, manifest),
        "tasks": task_matches(normalized, tasks),
        "knowledge_topics": knowledge_matches(normalized, knowledge),
        "test_candidates": test_candidates(normalized),
        "next_commands": [
            f"workspace changes verify <task-id> --agent codex",
            f"workspace knowledge find \"{Path(normalized).stem}\"",
        ],
    }


def score_topic(query: str, topic_id: str, topic: dict[str, Any]) -> int:
    haystack = " ".join(
        [
            topic_id,
            str(topic.get("title", "")),
            " ".join(str(alias) for alias in topic.get("aliases", []) or []),
            " ".join(
                str(entry.get("path", "")) + " " + str(entry.get("purpose", ""))
                for entry in topic.get("entries", []) or []
                if isinstance(entry, dict)
            ),
        ]
    ).casefold()
    terms = [term for term in query.casefold().split() if term]
    return sum(1 for term in terms if term in haystack)


def explain_topic(query: str, limit: int) -> dict[str, Any]:
    registry = load_yaml(KNOWLEDGE_REGISTRY_PATH)
    matches = []
    for topic_id, topic in (registry.get("topics") or {}).items():
        score = score_topic(query, topic_id, topic)
        if score:
            matches.append({"id": topic_id, "score": score, **topic})
    matches.sort(key=lambda row: (-int(row["score"]), str(row["id"])))
    return {
        "mode": "topic",
        "query": query,
        "matches": matches[:limit],
        "next_commands": [
            f"workspace knowledge find \"{query}\"",
            "workspace explain path <returned-path>",
        ],
    }


def explain_mechanism(name: str) -> dict[str, Any]:
    key = name.casefold().replace("_", "-")
    if key not in MECHANISMS:
        return {
            "mode": "mechanism",
            "name": key,
            "error": "unknown mechanism",
            "known_mechanisms": sorted(MECHANISMS),
        }
    return {"mode": "mechanism", "name": key, **MECHANISMS[key]}


def print_list(label: str, values: list[str]) -> None:
    print(label)
    if not values:
        print("  - None found.")
        return
    for value in values:
        print(f"  - {value}")


def render_path(result: dict[str, Any]) -> None:
    print(f"Path: {result['path']}")
    print(f"Exists: {'yes' if result['exists'] else 'no'}")
    print(f"Layer: {result['layer']}")
    print_list("Manifest matches:", result["manifest_matches"])
    print("Related tasks:")
    if result["tasks"]:
        for row in result["tasks"]:
            print(f"  - {row['id']} ({row['reason']}): {row['summary']}")
    else:
        print("  - None found.")
    print("Knowledge topics:")
    if result["knowledge_topics"]:
        for row in result["knowledge_topics"]:
            print(f"  - {row['topic']}: {row['purpose']}")
    else:
        print("  - None found.")
    print_list("Likely tests:", result["test_candidates"])
    print_list("Next commands:", result["next_commands"])


def render_topic(result: dict[str, Any]) -> None:
    print(f"Topic query: {result['query']}")
    if not result["matches"]:
        print("No registered knowledge topics matched.")
    for match in result["matches"]:
        print(f"\n{match['id']}: {match.get('title', '')} (score {match['score']})")
        for entry in match.get("entries", []) or []:
            print(f"  - {entry.get('path')} [{entry.get('layer', '')}]")
            print(f"    {entry.get('purpose', '')}")
    print("")
    print_list("Next commands:", result["next_commands"])


def render_mechanism(result: dict[str, Any]) -> None:
    if result.get("error"):
        print(f"Unknown mechanism: {result['name']}")
        print_list("Known mechanisms:", result["known_mechanisms"])
        return
    print(f"Mechanism: {result['title']}")
    print(f"Purpose: {result['purpose']}")
    print_list("Entrypoints:", result["entrypoints"])
    print_list("Sources:", result["sources"])
    print_list("Checks:", result["checks"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Explain workspace paths, topics, and mechanisms.")
    parser.add_argument("--format", dest="global_format", choices=("text", "json"))
    commands = parser.add_subparsers(dest="command", required=True)
    path = commands.add_parser("path", help="Explain one workspace-relative path.")
    path.add_argument("path")
    path.add_argument("--format", choices=("text", "json"))
    topic = commands.add_parser("topic", help="Explain registered knowledge topics matching a query.")
    topic.add_argument("query")
    topic.add_argument("--limit", type=int, default=3)
    topic.add_argument("--format", choices=("text", "json"))
    mechanism = commands.add_parser("mechanism", help="Explain a named workspace mechanism.")
    mechanism.add_argument("name")
    mechanism.add_argument("--format", choices=("text", "json"))
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "path":
        result = explain_path(args.path)
        renderer = render_path
    elif args.command == "topic":
        result = explain_topic(args.query, max(1, args.limit))
        renderer = render_topic
    else:
        result = explain_mechanism(args.name)
        renderer = render_mechanism

    output_format = args.format or args.global_format or "text"
    if output_format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        renderer(result)
    return 1 if result.get("error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
