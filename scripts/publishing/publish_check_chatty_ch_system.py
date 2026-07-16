#!/usr/bin/env python3
"""Verify a generated Chatty Ch System public repository projection."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


REQUIRED_PATHS: set[str] = {
    "README.md",
    ".github/workflows/ci.yml",
    "scripts/check_public_package.py",
    "workspace_manifest.yaml.template",
    "shared/delivery_output_policy.md",
    "shared/discovery_rules.md",
    "shared/failure_policy.md",
    "shared/manifest_portability_policy.md",
    "shared/session_continuity_policy.md",
    "shared/workspace_path_policy.md",
    "packages/character-system/engineering/generation/character-generator/SKILL.md",
    "packages/character-system/engineering/generation/character-generator/scripts/build_character.py",
    "packages/character-system/engineering/generation/character-generator/tests/test_config_validation.py",
    "packages/character-system/engineering/diagnosis/style-doctor/SKILL.md",
    "packages/character-system/engineering/maintenance/character-maintainer/SKILL.md",
    "packages/character-system/shared/protocol_manifest.json",
}

FORBIDDEN_PATHS: set[str] = {
    "packages/character-system/runtime",
    "packages/character-system/reports",
    "packages/character-system/distribution",
    "packages/character-system/engineering/generation/character-generator/configs/writerA.json",
    "packages/character-system/engineering/corpus-preparation/qq-raw-material-filter",
}

FORBIDDEN_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"D:[\\/]+AI", re.IGNORECASE),
    re.compile(r"C:[\\/]+Users[\\/]+Z1377", re.IGNORECASE),
    re.compile(r"packages/character-system/runtime/characters", re.IGNORECASE),
    re.compile(r"zyc-toolkit", re.IGNORECASE),
    re.compile(r"\bZYC\b"),
    re.compile(r"\bzyc\b"),
]

ALLOWLISTED_TEXT_PATHS: set[str] = {
    "scripts/check_public_package.py",
}

TEXT_SUFFIXES: set[str] = {
    ".json",
    ".md",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
    ".toml",
    ".gitignore",
}


def is_text(path: Path) -> bool:
    return path.name == ".gitignore" or path.suffix.lower() in TEXT_SUFFIXES


def check_required(root: Path) -> list[str]:
    return [
        f"Missing required path: {rel}"
        for rel in sorted(REQUIRED_PATHS)
        if not (root / rel).is_file()
    ]


def check_forbidden_paths(root: Path) -> list[str]:
    return [
        f"Forbidden path exists: {rel}"
        for rel in sorted(FORBIDDEN_PATHS)
        if (root / rel).exists()
    ]


def check_forbidden_text(root: Path) -> list[str]:
    issues: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts or not is_text(path):
            continue
        rel = path.relative_to(root).as_posix()
        if rel in ALLOWLISTED_TEXT_PATHS:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in FORBIDDEN_PATTERNS:
            match = pattern.search(text)
            if match:
                line = text[: match.start()].count("\n") + 1
                issues.append(f"{rel}:{line}: matched {pattern.pattern!r}")
    return issues


def run_public_self_check(root: Path) -> list[str]:
    result = subprocess.run(
        [sys.executable, "scripts/check_public_package.py", "--dir", "."],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode == 0:
        return []
    return [f"Public self-check failed: {(result.stdout + result.stderr).strip()[-500:]}"]


def run_generator_tests(root: Path) -> list[str]:
    test_root = root / "packages/character-system/engineering/generation/character-generator"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-q"],
        cwd=test_root,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode == 0:
        return []
    return [f"Generator pytest failed: {(result.stdout + result.stderr).strip()[-500:]}"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a generated Chatty Ch System public projection.")
    parser.add_argument("--dir", required=True, help="Generated repository root.")
    parser.add_argument("--skip-tests", action="store_true", help="Skip generator pytest.")
    args = parser.parse_args()

    root = Path(args.dir).resolve()
    if not root.is_dir():
        print(f"ERROR: not a directory: {root}", file=sys.stderr)
        return 1

    checks: list[tuple[str, list[str]]] = [
        ("Required paths", check_required(root)),
        ("Forbidden paths", check_forbidden_paths(root)),
        ("Forbidden text", check_forbidden_text(root)),
        ("Public self-check", run_public_self_check(root)),
    ]
    if not args.skip_tests:
        checks.append(("Generator tests", run_generator_tests(root)))

    total = 0
    for name, issues in checks:
        if issues:
            print(f"(!) {name}: {len(issues)} issue(s)")
            for issue in issues:
                print(f"  {issue}")
            total += len(issues)
        else:
            print(f"(i) {name}: OK")

    if total:
        print(f"FAILED: {total} issue(s) found.")
        return 1
    print("PASSED: Chatty Ch System projection is ready to publish.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
