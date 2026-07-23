from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

import yaml


from scripts.workspace.project_context import TASK_LEDGER_ROOT, load_knowledge_registry, load_task_registry
from scripts.workspace.runtime import WORKSPACE_ROOT
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.workspace.workspace_cli import build_parser


MANIFEST_PATH = WORKSPACE_ROOT / "workspace_manifest.yaml"
TASK_REGISTRY_PATH = WORKSPACE_ROOT / "PROJECT_CONTEXT" / "tasks" / "registry" / "index.yaml"
KNOWLEDGE_REGISTRY_PATH = WORKSPACE_ROOT / "PROJECT_CONTEXT" / "knowledge" / "index.yaml"
LEDGER_PATH = TASK_LEDGER_ROOT

ENTRY_PATTERN = re.compile(
    r"^### (?P<id>TASK-\d{8}-\d+) - (?P<title>.+?)\n"
    r"(?P<body>.*?)(?=^### TASK-\d{8}-\d+ - |\Z)",
    re.MULTILINE | re.DOTALL,
)
FIELD_PATTERN = re.compile(r"^- (?P<name>Date|Status|Task type|Branch|Commit): (?P<value>.*)$", re.MULTILINE)


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected a mapping in {path}")
    return data


def git_output(args: Sequence[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=WORKSPACE_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def cli_commands() -> list[str]:
    parser = build_parser()
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return sorted(action.choices)
    return []


def parse_recent_ledger(path: Path = LEDGER_PATH, limit: int = 5) -> list[dict[str, str]]:
    paths = [path] if path.is_file() else sorted(path.glob("20??/??/??.md"), reverse=True)
    entries: list[dict[str, str]] = []
    for ledger_path in paths:
      for match in ENTRY_PATTERN.finditer(ledger_path.read_text(encoding="utf-8")):
        fields = {
            field.group("name").lower().replace(" ", "_"): field.group("value").strip()
            for field in FIELD_PATTERN.finditer(match.group("body"))
        }
        entries.append(
            {
                "id": match.group("id"),
                "title": match.group("title").strip(),
                **fields,
            }
        )
        if len(entries) >= max(1, limit): return entries
    return entries


def workspace_tag_state(workspace_version: str | None) -> tuple[str | None, int | None]:
    if not workspace_version:
        return None, None
    candidate = f"v{workspace_version}"
    tag = git_output(["describe", "--tags", "--match", candidate, "--abbrev=0"])
    if tag != candidate:
        return None, None
    count = git_output(["rev-list", "--count", f"{tag}..HEAD"])
    return tag, int(count) if count.isdigit() else None


def workspace_describe(workspace_version: str | None) -> str:
    if not workspace_version:
        return git_output(["describe", "--always", "--dirty"])
    return git_output(
        ["describe", "--tags", "--match", f"v{workspace_version}", "--always", "--dirty"]
    )


def build_summary(recent: int = 5) -> dict[str, Any]:
    manifest = load_yaml(MANIFEST_PATH)
    tasks = load_task_registry().get("tasks", {})
    topics = load_knowledge_registry().get("topics", {})
    workspace = manifest.get("workspace", {})
    workspace_version = workspace.get("workspace_version")
    workspace_tag, commits_ahead = workspace_tag_state(workspace_version)

    return {
        "workspace": {
            "name": workspace.get("workspace_name"),
            "version": workspace_version,
            "source_of_truth": workspace.get("source_of_truth"),
            "manifest": workspace.get("manifest_path", "workspace_manifest.yaml"),
        },
        "git": {
            "branch": git_output(["branch", "--show-current"]),
            "commit": git_output(["rev-parse", "--short", "HEAD"]),
            "describe": workspace_describe(workspace_version),
            "workspace_tag": workspace_tag,
            "commits_ahead": commits_ahead,
            "clean": not bool(git_output(["status", "--short", "--untracked-files=all"])),
        },
        "inventory": {
            "packages": len(manifest.get("packages", [])),
            "skills": len(manifest.get("skills", [])),
            "projections": len(manifest.get("projections", [])),
            "workspace_protocols": len(manifest.get("protocols", [])),
            "task_routes": len(tasks) if isinstance(tasks, dict) else 0,
            "knowledge_topics": len(topics) if isinstance(topics, dict) else 0,
            "cli_commands": cli_commands(),
        },
        "recent_governance": parse_recent_ledger(limit=recent),
        "authority_note": (
            "Live summary only: manifest owns workspace facts, Git owns version history, "
            "and the task ledger owns bounded continuity notes."
        ),
    }


def render_text(summary: dict[str, Any]) -> str:
    workspace = summary["workspace"]
    git = summary["git"]
    inventory = summary["inventory"]
    lines = [
        "Workspace Summary",
        f"  Name: {workspace['name']}",
        f"  Manifest version: {workspace['version']}",
        f"  Source of truth: {workspace['source_of_truth']}",
        "",
        "Git",
        f"  Branch: {git['branch'] or '(detached)'}",
        f"  Commit: {git['commit']}",
        f"  Describe: {git['describe']}",
        f"  Workspace tag: {git['workspace_tag'] or '(none)'}",
        f"  Commits ahead: {git['commits_ahead'] if git['commits_ahead'] is not None else '(unknown)'}",
        f"  Working tree: {'clean' if git['clean'] else 'modified'}",
        "",
        "Inventory",
        f"  Packages: {inventory['packages']}",
        f"  Skills: {inventory['skills']}",
        f"  Projections: {inventory['projections']}",
        f"  Workspace protocols: {inventory['workspace_protocols']}",
        f"  Task routes: {inventory['task_routes']}",
        f"  Knowledge topics: {inventory['knowledge_topics']}",
        f"  CLI commands: {', '.join(inventory['cli_commands'])}",
        "",
        "Recent Governance",
    ]
    for entry in summary["recent_governance"]:
        details = " | ".join(
            value
            for value in (
                entry.get("date"),
                entry.get("status"),
                entry.get("commit"),
            )
            if value
        )
        lines.append(f"  {entry['id']}: {entry['title']}" + (f" ({details})" if details else ""))
    lines.extend(["", summary["authority_note"]])
    return "\n".join(lines)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Show live workspace and governance facts.")
    parser.add_argument("--recent", type=int, default=5)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main() -> int:
    args = build_argument_parser().parse_args()
    summary = build_summary(recent=max(1, args.recent))
    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(render_text(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
