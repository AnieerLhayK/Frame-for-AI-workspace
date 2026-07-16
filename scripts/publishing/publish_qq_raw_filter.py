#!/usr/bin/env python3
"""Generate the public qq-chat-raw-filter repository projection."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from scripts.workspace.runtime import WORKSPACE_ROOT
SOURCE_REL = "packages/character-system/engineering/corpus-preparation/qq-raw-material-filter"
REPO_NAME = "qq-chat-raw-filter"

from scripts.publishing.publish_public import scrub_content
from scripts.publishing.qq_raw_filter_public_checks import render_generated_check_script

TEXT_SUFFIXES = {".json", ".md", ".py", ".txt", ".toml", ".yaml", ".yml", ".gitignore"}
SKIP_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".git"}


def is_text_file(path: Path) -> bool:
    return path.name == ".gitignore" or path.suffix.lower() in TEXT_SUFFIXES


def should_skip(path: Path, source_root: Path) -> bool:
    rel = path.relative_to(source_root)
    if any(part in SKIP_PARTS for part in rel.parts):
        return True
    if any(part.endswith(".egg-info") for part in rel.parts):
        return True
    if rel.parts and rel.parts[0] in {"corpus", "output"}:
        return True
    if "debug" in rel.parts and path.name != ".gitkeep":
        return True
    return path.is_file() and path.suffix.lower() == ".pyc"


def publicize_text(text: str) -> str:
    return scrub_content(text)


def clear_output(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for child in out_dir.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def copy_tree(source_root: Path, out_dir: Path) -> None:
    if not source_root.is_dir():
        raise FileNotFoundError(f"qq raw filter source is missing: {source_root}")
    for source in source_root.rglob("*"):
        if not source.is_file() or should_skip(source, source_root):
            continue
        target = out_dir / source.relative_to(source_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        if is_text_file(source):
            target.write_text(publicize_text(source.read_text(encoding="utf-8", errors="replace")), encoding="utf-8", newline="\n")
        else:
            shutil.copy2(source, target)


def generate(out_dir: Path) -> None:
    clear_output(out_dir)
    copy_tree(WORKSPACE_ROOT / SOURCE_REL, out_dir)
    check_path = out_dir / "scripts" / "check_public_package.py"
    check_path.parent.mkdir(parents=True, exist_ok=True)
    check_path.write_text(render_generated_check_script(), encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the qq-chat-raw-filter public projection.")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    out_dir = Path(args.out_dir).resolve()
    generate(out_dir)
    print(f"Generated {REPO_NAME} public projection at {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
