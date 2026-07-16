#!/usr/bin/env python3
"""Discover the workspace root by bounded parent lookup."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_MAX_PARENT_DEPTH = 5
DEFAULT_MANIFEST_FILENAME = "workspace_manifest.yaml"


def read_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def find_manifest(start: Path, filename: str, max_depth: int) -> tuple[Path | None, list[Path]]:
    current = start.resolve()
    if current.is_file():
        current = current.parent

    attempts: list[Path] = []
    for _depth in range(max_depth + 1):
        candidate = current / filename
        attempts.append(candidate)
        if candidate.is_file():
            return candidate, attempts
        if current.parent == current:
            break
        current = current.parent
    return None, attempts


def resolve_workspace_path(workspace_root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return workspace_root / Path(value.replace("/", "\\"))


def build_result(manifest_path: Path) -> dict[str, Any]:
    manifest = read_manifest(manifest_path)
    workspace_root = manifest_path.parent.resolve()
    shared_root = resolve_workspace_path(workspace_root, str(manifest["shared"]["source_path"]))
    platform_roots = manifest.get("platform_roots", {})

    result = {
        "workspace_root": str(workspace_root),
        "manifest_path": str(manifest_path.resolve()),
        "shared_root": str(shared_root.resolve()),
        "platform_roots": {str(key): str(value) for key, value in platform_roots.items()},
        "source_of_truth": str(manifest.get("workspace", {}).get("source_of_truth", "")),
    }
    # Compatibility aliases for callers written against manifest format 1.0.
    result["codex_skills_root"] = str(platform_roots.get("codex", ""))
    result["opencode_skills_root"] = str(platform_roots.get("opencode", ""))
    return result


def print_text_result(result: dict[str, Any]) -> None:
    print("Workspace bootstrap discovery succeeded.")
    for key in [
        "workspace_root",
        "manifest_path",
        "shared_root",
        "source_of_truth",
    ]:
        print(f"{key}: {result.get(key, '')}")
    print("platform_roots:")
    for platform, root in result.get("platform_roots", {}).items():
        print(f"  {platform}: {root}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover workspace_manifest.yaml by bounded parent lookup.")
    parser.add_argument("--start", default=".", help="Start directory or file. Default: current directory.")
    parser.add_argument("--max-parent-depth", type=int, default=DEFAULT_MAX_PARENT_DEPTH)
    parser.add_argument("--manifest-filename", default=DEFAULT_MANIFEST_FILENAME)
    parser.add_argument("--print-json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    start = Path(args.start)
    manifest_path, attempts = find_manifest(start, args.manifest_filename, args.max_parent_depth)

    if manifest_path is None:
        payload = {
            "error": "workspace manifest not found",
            "start": str(start.resolve()),
            "max_parent_depth": args.max_parent_depth,
            "manifest_filename": args.manifest_filename,
            "attempts": [str(path) for path in attempts],
            "action": "Run from inside the workspace, pass --start to a workspace child path, or restore workspace_manifest.yaml.",
        }
        if args.print_json:
            print(json.dumps(payload, indent=2))
        else:
            print("[ERROR]")
            print("workspace_manifest.yaml was not found by bounded parent lookup.")
            print(f"Start: {payload['start']}")
            print(f"Max parent depth: {args.max_parent_depth}")
            print("Discovery attempts:")
            for path in attempts:
                print(f"- {path}")
            print("Action:")
            print(payload["action"])
        return 1

    try:
        result = build_result(manifest_path)
    except Exception as exc:
        print(f"[ERROR]\nFailed to parse discovered manifest:\n{manifest_path}\n\nReason:\n{exc}")
        return 1

    if args.print_json:
        print(json.dumps(result, indent=2))
    else:
        print_text_result(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
