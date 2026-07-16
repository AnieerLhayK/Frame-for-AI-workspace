#!/usr/bin/env python3
"""Generate the public Chatty Ch System repository from workspace sources.

The generated repository is a disposable projection, not a source tree. Source
ownership stays in this workspace; the public repository receives only the
character-system engineering layer, package-level shared protocols, portable
root policies, docs, CI, and a public self-check.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from scripts.workspace.runtime import WORKSPACE_ROOT

from scripts.publishing.publish_public import scrub_content

REPO_NAME = "Chatty-Ch-System"
FRAME_REPO_URL = "https://github.com/AnieerLhayK/Frame-for-AI-workspace"

COPY_DIRS: tuple[tuple[str, str], ...] = (
    ("packages/character-system/engineering", "packages/character-system/engineering"),
    ("packages/character-system/shared", "packages/character-system/shared"),
)

ROOT_SHARED_FILES: tuple[str, ...] = (
    "shared/delivery_output_policy.md",
    "shared/discovery_rules.md",
    "shared/failure_policy.md",
    "shared/manifest_portability_policy.md",
    "shared/session_continuity_policy.md",
    "shared/workspace_path_policy.md",
)

EXCLUDED_REL_PATHS: set[str] = {
    "packages/character-system/engineering/generation/character-generator/configs/writerA.json",
    "packages/character-system/engineering/corpus-preparation/qq-raw-material-filter",
}

EXCLUDED_PARTS: set[str] = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "corpus",
    "_private",
    "_drafts",
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

PUBLIC_TEXT_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("packages/character-system/runtime/characters", "local-runtime-character-output"),
    ("ZYC-specific", "character-specific"),
    ("zyc-specific", "character-specific"),
    ("ZYC", "target character"),
    ("zyc", "target-character"),
    ("writerA", "sample-character"),
    ("Writer A", "Sample Character"),
    ("Writer-A", "Sample-Character"),
    ("zf-style", "sample-style"),
    ("zf", "sample-style"),
)


def is_text_file(path: Path) -> bool:
    if path.name in {".gitignore"}:
        return True
    return path.suffix.lower() in TEXT_SUFFIXES


def publicize_text(text: str) -> str:
    text = scrub_content(text)
    for source, replacement in PUBLIC_TEXT_REPLACEMENTS:
        text = text.replace(source, replacement)
    return text


def should_skip(path: Path, source_root: Path) -> bool:
    rel = path.relative_to(source_root).as_posix()
    if any(rel == excluded or rel.startswith(excluded + "/") for excluded in EXCLUDED_REL_PATHS):
        return True
    return any(part in EXCLUDED_PARTS for part in path.parts)


def clear_output(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for child in out_dir.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def write_file(root: Path, rel_path: str, content: str) -> None:
    target = root / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="\n")


def copy_public_path(source: Path, dest: Path, source_root: Path) -> None:
    if should_skip(source, source_root):
        return
    if source.is_dir():
        return

    dest.parent.mkdir(parents=True, exist_ok=True)
    if is_text_file(source):
        dest.write_text(
            publicize_text(source.read_text(encoding="utf-8", errors="replace")),
            encoding="utf-8",
            newline="\n",
        )
    else:
        shutil.copy2(source, dest)


def copy_tree(source_rel: str, dest_rel: str, out_dir: Path) -> None:
    source_root = WORKSPACE_ROOT / source_rel
    for source in source_root.rglob("*"):
        if should_skip(source, WORKSPACE_ROOT):
            continue
        if not source.is_file():
            continue
        rel = source.relative_to(source_root)
        copy_public_path(source, out_dir / dest_rel / rel, WORKSPACE_ROOT)


def generate_readme(repo_name: str) -> str:
    return f"""# Chatty Ch System

## Related Public Projects

- [Frame-for-AI-workspace](https://github.com/AnieerLhayK/Frame-for-AI-workspace):
  the deployable governed-workspace framework.
- [qq-chat-raw-filter](https://github.com/AnieerLhayK/qq-chat-raw-filter): the
  separately maintained corpus-preparation tool.

Chatty Ch System is the public engineering layer of a character-skill system for
building, diagnosing, and maintaining style-inspired chatting and writing bots.
It intentionally ships no finished character, private corpus, runtime memory, or
personal material.

The workspace package README remains the source-facing contract. This README is
generated for the public projection; update the source package and run the
registered publisher instead of editing a staging checkout by hand.

This repository is best used inside
[Frame for AI Workspace]({FRAME_REPO_URL}), where routing, shared policy,
validation, and workspace migration rules are already in place. The system can
also be copied into another governed workspace if you preserve the package
layout and shared protocols.

## What Is Included

- `packages/character-system/engineering/generation/character-generator`: build
  a character skill from an authorized or public corpus.
- `packages/character-system/engineering/diagnosis/style-doctor`: diagnose
  style drift and runtime output failures.
- `packages/character-system/engineering/maintenance/character-maintainer`:
  maintain generated skills across patches and version changes.
- The companion [`qq-chat-raw-filter`](https://github.com/AnieerLhayK/qq-chat-raw-filter)
  repository is maintained separately while its corpus-preparation tool is
  being completed. It is intentionally excluded from this projection for now;
  after completion it can be evaluated for inclusion through a separate
  privacy, portability, and CI review.
- `packages/character-system/shared`: schemas, templates, drift taxonomy,
  patch protocol, handoff format, and runtime-loop policy.
- `shared`: portable root-level workspace policies needed to understand how the
  package is meant to be moved and governed.

## What Is Not Included

- No runtime character folders.
- No private or personal corpus.
- No diagnosis, handoff, validation, or patch reports from a private workspace.
- No distribution bundle such as a finished toolkit release.
- No local absolute paths or machine-specific configuration.

## Quick Check

```bash
python scripts/check_public_package.py --dir .
cd packages/character-system/engineering/generation/character-generator
python -m pytest tests -q
```

## Basic Use

1. Put authorized or public source material in an ignored local `corpus/`
   directory.
2. Copy `configs/character_config.example.json` to a private config path and
   edit the character id, display name, corpus sources, target tasks, and
   privacy settings.
3. Run the generator from
   `packages/character-system/engineering/generation/character-generator`.
4. Inspect the generated skill and reports before exposing it to any runtime
   platform.

Generated character skills are style-inspired writing tools. They are not
identity simulators, impersonation bots, private fact inference tools, or corpus
reconstruction tools.
"""


def generate_gitignore() -> str:
    return """# Local corpora and generated characters
corpus/
characters/
packages/character-system/engineering/generation/character-generator/corpus/
packages/character-system/engineering/generation/character-generator/characters/*
!packages/character-system/engineering/generation/character-generator/characters/.gitkeep

# Private configs and local plans
*.local.json
*.draft.json
configs/_private/
configs/_drafts/
packages/character-system/engineering/generation/character-generator/configs/_private/
packages/character-system/engineering/generation/character-generator/configs/_drafts/

# Python/tooling caches
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
*.pyc

# Local environment
.env
.venv/
venv/
"""


def generate_ci() -> str:
    return """name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install test dependency
        run: python -m pip install --upgrade pytest
      - name: Check public package boundaries
        run: python scripts/check_public_package.py --dir .
      - name: Run generator tests
        working-directory: packages/character-system/engineering/generation/character-generator
        run: python -m pytest tests -q
"""


def generate_check_script() -> str:
    return '''#!/usr/bin/env python3
"""Validate that this public package contains no private character artifacts."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_PATHS = {
    "README.md",
    ".github/workflows/ci.yml",
    "packages/character-system/engineering/generation/character-generator/SKILL.md",
    "packages/character-system/engineering/diagnosis/style-doctor/SKILL.md",
    "packages/character-system/engineering/maintenance/character-maintainer/SKILL.md",
    "packages/character-system/shared/protocol_manifest.json",
    "shared/delivery_output_policy.md",
}

FORBIDDEN_PATHS = {
    "packages/character-system/runtime",
    "packages/character-system/reports",
    "packages/character-system/distribution",
    "packages/character-system/engineering/generation/character-generator/configs/writerA.json",
    "packages/character-system/engineering/corpus-preparation/qq-raw-material-filter",
}

FORBIDDEN_TEXT = [
    re.compile(r"D:[\\\\/]+AI", re.IGNORECASE),
    re.compile(r"C:[\\\\/]+Users[\\\\/]+Z1377", re.IGNORECASE),
    re.compile(r"packages/character-system/runtime/characters", re.IGNORECASE),
    re.compile(r"zyc-toolkit", re.IGNORECASE),
    re.compile(r"\\bZYC\\b"),
    re.compile(r"\\bzyc\\b"),
]

SKIP_TEXT_SCAN = {
    "scripts/check_public_package.py",
}

TEXT_SUFFIXES = {".json", ".md", ".py", ".txt", ".yaml", ".yml", ".toml", ".gitignore"}


def is_text(path: Path) -> bool:
    return path.name == ".gitignore" or path.suffix.lower() in TEXT_SUFFIXES


def check_required(root: Path) -> list[str]:
    return [f"Missing required path: {rel}" for rel in sorted(REQUIRED_PATHS) if not (root / rel).is_file()]


def check_forbidden_paths(root: Path) -> list[str]:
    issues = []
    for rel in sorted(FORBIDDEN_PATHS):
        if (root / rel).exists():
            issues.append(f"Forbidden path exists: {rel}")
    return issues


def check_text(root: Path) -> list[str]:
    issues = []
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts or not is_text(path):
            continue
        rel = path.relative_to(root).as_posix()
        if rel in SKIP_TEXT_SCAN:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in FORBIDDEN_TEXT:
            match = pattern.search(text)
            if match:
                line = text[: match.start()].count("\\n") + 1
                issues.append(f"{rel}:{line}: forbidden text matched {pattern.pattern!r}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".", help="Repository root to validate.")
    args = parser.parse_args()
    root = Path(args.dir).resolve()

    issues = []
    issues.extend(check_required(root))
    issues.extend(check_forbidden_paths(root))
    issues.extend(check_text(root))

    if issues:
        print("FAILED: public package boundary check found issues:")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    print("PASSED: public package boundary check.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def generate_manifest_template(repo_name: str) -> str:
    return f"""schema_version: "0.1"
workspace:
  name: "{repo_name}"
  source_of_truth: "${{WORKSPACE_ROOT}}"
  description: "Public engineering layer for portable character-skill generation, diagnosis, and maintenance."

external_ecosystem:
  frame_for_ai_workspace: "{FRAME_REPO_URL}"

packages:
  - id: character-system
    path: packages/character-system
    included_layers:
      - engineering
      - shared
    excluded_layers:
      - runtime characters
      - private reports
      - distribution bundles
"""


def generate(out_dir: Path, repo_name: str = REPO_NAME) -> None:
    clear_output(out_dir)

    for source_rel, dest_rel in COPY_DIRS:
        copy_tree(source_rel, dest_rel, out_dir)

    for rel in ROOT_SHARED_FILES:
        source = WORKSPACE_ROOT / rel
        if source.is_file():
            copy_public_path(source, out_dir / rel, WORKSPACE_ROOT)

    write_file(out_dir, "README.md", generate_readme(repo_name))
    write_file(out_dir, ".gitignore", generate_gitignore())
    write_file(out_dir, ".github/workflows/ci.yml", generate_ci())
    write_file(out_dir, "scripts/check_public_package.py", generate_check_script())
    write_file(out_dir, "workspace_manifest.yaml.template", generate_manifest_template(repo_name))


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the Chatty Ch System public repository projection.")
    parser.add_argument("--out-dir", required=True, help="Output directory for the generated repository.")
    parser.add_argument("--repo-name", default=REPO_NAME, help="Repository name to use in generated docs.")
    args = parser.parse_args()

    out_dir = Path(args.out_dir).resolve()
    generate(out_dir, args.repo_name)
    print(f"Generated {args.repo_name} public projection at {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
