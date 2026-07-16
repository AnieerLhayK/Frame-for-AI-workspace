from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

import yaml


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = WORKSPACE_ROOT / "PROJECT_CONTEXT" / "doc_pair_registry.yaml"
ZH_SUFFIX = ".zh-CN.md"
MD_SUFFIX = ".md"


def normalize_path(value: str | Path) -> str:
    return str(value).replace("\\", "/").strip("/")


def is_markdown(path: str) -> bool:
    return path.endswith(MD_SUFFIX)


def is_zh_companion(path: str) -> bool:
    return path.endswith(ZH_SUFFIX)


def companion_for(primary: str) -> str:
    if not primary.endswith(MD_SUFFIX) or primary.endswith(ZH_SUFFIX):
        raise ValueError(f"not a Markdown primary: {primary}")
    return f"{primary[:-len(MD_SUFFIX)]}{ZH_SUFFIX}"


def primary_for(companion: str) -> str:
    if not companion.endswith(ZH_SUFFIX):
        raise ValueError(f"not a zh-CN companion: {companion}")
    return f"{companion[:-len(ZH_SUFFIX)]}{MD_SUFFIX}"


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("doc pair registry must be a mapping")
    payload.setdefault("directories", [])
    payload.setdefault("pairs", [])
    return payload


def path_under(path: str, directory: str) -> tuple[bool, str]:
    path = normalize_path(path)
    directory = normalize_path(directory)
    if not directory:
        return True, path
    if path == directory:
        return True, ""
    prefix = f"{directory}/"
    if path.startswith(prefix):
        return True, path[len(prefix) :]
    return False, ""


def matches_directory_rule(path: str, rule: dict[str, Any]) -> bool:
    under, remainder = path_under(path, str(rule.get("path", "")))
    if not under or not remainder:
        return False
    if not rule.get("recursive", False) and "/" in remainder:
        return False
    pattern = str(rule.get("pattern", "*.md"))
    name = PurePosixPath(remainder).name
    return fnmatch.fnmatchcase(name, pattern) or fnmatch.fnmatchcase(remainder, pattern)


def exact_pairs(registry: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for pair in registry.get("pairs", []):
        primary = normalize_path(str(pair.get("primary", "")))
        companion = normalize_path(str(pair.get("companion", "")))
        if primary and companion:
            result[primary] = companion
    return result


def primary_is_registered(path: str, registry: dict[str, Any]) -> bool:
    path = normalize_path(path)
    if path in exact_pairs(registry):
        return True
    return any(matches_directory_rule(path, rule) for rule in registry.get("directories", []))


def companion_is_registered(path: str, registry: dict[str, Any]) -> bool:
    path = normalize_path(path)
    pairs = exact_pairs(registry)
    if path in pairs.values():
        return True
    return primary_is_registered(primary_for(path), registry)


def iter_existing_companions(root: Path) -> list[str]:
    ignored_parts = {".git"}
    companions: list[str] = []
    for path in root.rglob(f"*{ZH_SUFFIX}"):
        relative = path.relative_to(root)
        if ignored_parts & set(relative.parts):
            continue
        companions.append(normalize_path(relative))
    return sorted(companions)


def validate_existing_coverage(root: Path, registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for companion in iter_existing_companions(root):
        primary = primary_for(companion)
        if not (root / primary).exists():
            errors.append(f"zh-CN companion has no primary Markdown file: {companion} -> {primary}")
            continue
        if not companion_is_registered(companion, registry):
            errors.append(f"existing zh-CN companion is not registered: {companion}")
    return errors


def changed_paths_from_git(root: Path) -> list[tuple[str, str]]:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    changes: list[tuple[str, str]] = []
    for line in completed.stdout.splitlines():
        if not line:
            continue
        status = line[:2]
        path = line[3:]
        if " -> " in path:
            path = path.rsplit(" -> ", 1)[1]
        changes.append((status, normalize_path(path.strip('"'))))
    return changes


def analyze_changes(
    root: Path,
    registry: dict[str, Any],
    changes: list[tuple[str, str]],
    strict: bool = False,
) -> dict[str, Any]:
    changed = {path for _, path in changes}
    warnings: list[str] = []
    errors: list[str] = []

    for status, path in sorted(changes, key=lambda item: item[1]):
        if not is_markdown(path):
            continue
        if is_zh_companion(path):
            if not companion_is_registered(path, registry):
                errors.append(f"unregistered zh-CN companion changed: {path}")
            continue
        if not primary_is_registered(path, registry):
            continue
        companion = companion_for(path)
        if (root / companion).exists() and companion not in changed:
            message = f"registered Markdown primary changed without companion: {path} -> {companion}"
            if strict:
                errors.append(message)
            else:
                warnings.append(message)

    return {
        "status": "ERROR" if errors else "PASS",
        "warnings": warnings,
        "errors": errors,
        "checked_changes": [path for _, path in changes if is_markdown(path)],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check registered Markdown zh-CN companion edits.")
    parser.add_argument("--registry", default=str(REGISTRY_PATH))
    parser.add_argument("--root", default=str(WORKSPACE_ROOT))
    parser.add_argument("--strict", action="store_true", help="Treat unsynced companions as errors.")
    parser.add_argument(
        "--validate-coverage",
        action="store_true",
        help="Check that existing .zh-CN.md files are covered by the registry.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = Path(args.root)
    try:
        registry = load_registry(Path(args.registry))
        payload = analyze_changes(root, registry, changed_paths_from_git(root), strict=args.strict)
        if args.validate_coverage:
            coverage_errors = validate_existing_coverage(root, registry)
            payload["errors"].extend(coverage_errors)
            payload["status"] = "ERROR" if payload["errors"] else "PASS"
    except (OSError, ValueError, subprocess.CalledProcessError, yaml.YAMLError) as exc:
        payload = {"status": "ERROR", "errors": [str(exc)], "warnings": []}

    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"Status: {payload['status']}")
        for warning in payload.get("warnings", []):
            print(f"WARNING: {warning}")
        for error in payload.get("errors", []):
            print(f"ERROR: {error}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
