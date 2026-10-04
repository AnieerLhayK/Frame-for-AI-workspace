#!/usr/bin/env python3
"""
publish_public.py — Generate a scrubbed public-workspace skeleton.

Copies the workspace architecture, strips business code, replaces absolute
paths with template variables, and produces a git-ready public repository.

Usage:
    python -m scripts.publishing.publish_public --out-dir <path> [--repo-name <name>]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from scripts.workspace.runtime import WORKSPACE_ROOT

# Stable compatibility exports; implementations live at their owning seam.
from scripts.publishing.publish_policy import (
    EXCLUDED_PATHS,
    PUBLIC_EXTENSION_LAYERS,
    SCRUB_FILES,
    SKELETON_DIRS,
    SUBSTITUTIONS,
    TEMPLATE_FILES,
    _compile_substitutions,
    is_skeleton_dir,
    is_template,
    needs_scrub,
    scrub_content,
    should_exclude,
)
from scripts.publishing.public_workspace_renderer import (
    EXTENSION_LAYER_READMES,
    PUBLIC_QUICK_START_ROOT,
    PUBLIC_TEMPLATE_REPO_NAME,
    SKELETON_STUB,
    _read_public_guide_source,
    generate_beginner_guide_md,
    generate_onboarding_md,
    generate_path_mapping_md,
    generate_public_agent_guidance,
    generate_public_architecture_md,
    generate_public_manifest,
    generate_public_readme,
    generate_public_readme_zh,
    generate_public_setup_py,
)


def write_file(out_dir: Path, rel_path: str, content: str) -> None:
    """Write text content to a file under out_dir."""
    target = (out_dir / rel_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def projection_source_record(publisher: str, generator: str) -> str:
    """Return public-safe provenance for a generated projection."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=WORKSPACE_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode or not result.stdout.strip():
        raise RuntimeError("cannot resolve workspace source revision")
    return json.dumps(
        {
            "schema_version": "1.0",
            "source_revision": result.stdout.strip(),
            "publisher": publisher,
            "generator": generator,
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def copy_and_scrub(src_root: Path, out_dir: Path, rel_path: str) -> None:
    """Copy a file, scrubbing its content in transit."""
    src = (src_root / rel_path).resolve()
    content = src.read_text(encoding="utf-8")
    scrubbed = scrub_content(content)
    write_file(out_dir, rel_path, scrubbed)


def create_required_public_context_dirs(out_dir: Path) -> None:
    """Keep empty canonical task directories visible in the public skeleton."""
    for relative in ("PROJECT_CONTEXT/tasks/ledger", "PROJECT_CONTEXT/tasks/records"):
        placeholder = out_dir / relative / ".gitkeep"
        placeholder.parent.mkdir(parents=True, exist_ok=True)
        placeholder.write_text("", encoding="utf-8")


def strip_skeleton_dir(
    out_dir: Path, rel_path: str, stub_files: list[str], purpose: str
) -> None:
    """Clear a skeleton directory and replace with stub files."""
    target = (out_dir / rel_path).resolve()
    if target.is_dir():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    dir_name = target.name
    for fname in stub_files:
        stub_content = SKELETON_STUB.get(fname, "# {dir_name}\n\nStub file.\n")
        content = stub_content.replace("{dir_name}", dir_name)
        (target / fname).write_text(content, encoding="utf-8")
    if not stub_files:
        # Write a basic README if no stubs specified
        readme = target / "README.md"
        readme.write_text(
            f"# {dir_name}\n\n{purpose}\n\n"
            "This directory is a structural skeleton. "
            "Add your own content following the patterns in the workspace.\n",
            encoding="utf-8",
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a scrubbed public-workspace skeleton."
    )
    parser.add_argument(
        "--out-dir", required=True,
        help="Output directory for the generated public workspace.",
    )
    parser.add_argument(
        "--repo-name", default="governed-skill-workspace-template",
        help="Repository name (used in generated docs).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Only list actions without copying.",
    )
    args = parser.parse_args()

    # Verify we are in the workspace root
    workspace_root = Path.cwd().resolve()
    manifest_path = workspace_root / "workspace_manifest.yaml"
    if not manifest_path.is_file():
        print(
            "ERROR: must be run from workspace root (workspace_manifest.yaml not found).",
            file=sys.stderr,
        )
        return 1

    out_dir = Path(args.out_dir).resolve()
    repo_name = args.repo_name

    if out_dir == workspace_root or workspace_root in out_dir.parents:
        print("ERROR: output directory must be outside the source workspace.", file=sys.stderr)
        return 1

    print(f"Publishing from: {workspace_root}")
    print(f"Output to:      {out_dir}")
    print(f"Repo name:      {repo_name}")
    print()

    if args.dry_run:
        print("DRY RUN — no files will be written")
        print()

    counts: dict[str, int] = {"copied": 0, "scrubbed": 0, "templated": 0, "stripped": 0}
    warnings: list[str] = []

    # Walk the workspace and process each file
    for dirpath, dirnames, filenames in os.walk(workspace_root):
        # Skip .git
        if ".git" in dirnames:
            dirnames.remove(".git")

        # Compute relative directory
        rel_dir = os.path.relpath(dirpath, workspace_root).replace("\\", "/")
        if rel_dir == ".":
            rel_dir = ""

        # Prune excluded directories early
        top = rel_dir.split("/")[0] if rel_dir else ""
        if top in EXCLUDED_PATHS or rel_dir in EXCLUDED_PATHS:
            dirnames.clear()
            continue

        # Prune skeleton directories (we handle them separately)
        skip_dir = False
        for sdir, _stub_files, _purpose in SKELETON_DIRS:
            if rel_dir == sdir or rel_dir.startswith(sdir + "/"):
                skip_dir = True
                break
        if skip_dir:
            dirnames.clear()
            continue

        for fname in filenames:
            rel_path = (rel_dir + "/" + fname) if rel_dir else fname

            if should_exclude(rel_path):
                continue

            src_file = Path(dirpath) / fname
            rel_path_norm = rel_path.replace("\\", "/")

            # Rebuild the manifest below from a public-safe projection instead
            # of copying the private package and skill registry.
            if rel_path_norm == "workspace_manifest.yaml":
                continue

            if args.dry_run:
                # Classify what would happen
                if needs_scrub(rel_path_norm):
                    kind = "SCRUB"
                elif is_template(rel_path_norm):
                    kind = "TEMPLATE"
                else:
                    kind = "COPY"
                # Check skeleton
                sdir_purpose = is_skeleton_dir(rel_path_norm)
                if sdir_purpose:
                    kind = "STRIP"
                print(f"  [{kind}] {rel_path_norm}")
                continue

            # Check if this file falls inside a skeleton directory
            # (files IN skeleton dirs are excluded)
            in_skeleton = False
            for sdir, _stub_files, _purpose in SKELETON_DIRS:
                if rel_path_norm.startswith(sdir + "/"):
                    in_skeleton = True
                    break
            if in_skeleton:
                continue

            # Copy with or without scrubbing
            if needs_scrub(rel_path_norm):
                try:
                    copy_and_scrub(workspace_root, out_dir, rel_path_norm)
                    counts["scrubbed"] += 1
                except (OSError, UnicodeDecodeError) as exc:
                    warnings.append(f"Failed to scrub {rel_path_norm}: {exc}")
                    # Fall back to direct binary copy
                    try:
                        target = (out_dir / rel_path_norm).resolve()
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_file, target)
                        counts["copied"] += 1
                    except OSError as exc2:
                        warnings.append(f"Failed to copy {rel_path_norm}: {exc2}")
            else:
                try:
                    target = (out_dir / rel_path_norm).resolve()
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, target)
                    counts["copied"] += 1
                except OSError as exc:
                    warnings.append(f"Failed to copy {rel_path_norm}: {exc}")

    # Handle template file generation (create .template variants)
    if not args.dry_run:
        for tf in TEMPLATE_FILES:
            template_rel = tf + ".template"
            tf_norm = tf.replace("\\", "/")
            src_file = workspace_root / tf_norm
            if not src_file.is_file():
                warnings.append(f"Template source not found: {tf_norm}")
                continue
            try:
                if tf_norm == "workspace_manifest.yaml":
                    scrubbed = generate_public_manifest(src_file)
                else:
                    content = src_file.read_text(encoding="utf-8")
                    scrubbed = scrub_content(content)
                write_file(out_dir, template_rel, scrubbed)
                counts["templated"] += 1
            except OSError as exc:
                warnings.append(f"Failed to create template {template_rel}: {exc}")

    # Handle skeleton directories
    if not args.dry_run:
        for sdir, stub_files, purpose in SKELETON_DIRS:
            strip_skeleton_dir(out_dir, sdir, stub_files, purpose)
            counts["stripped"] += 1

    # Generate metadata documents
    if not args.dry_run:
        public_manifest = generate_public_manifest(manifest_path)
        write_file(out_dir, "workspace_manifest.yaml", public_manifest)
        write_file(out_dir, "README.md", generate_public_readme(repo_name))
        write_file(out_dir, "README.zh-CN.md", generate_public_readme_zh(repo_name))
        write_file(out_dir, "ARCHITECTURE.md", generate_public_architecture_md())
        write_file(out_dir, "AGENTS.md", generate_public_agent_guidance("AGENTS.md"))
        write_file(out_dir, "CLAUDE.md", generate_public_agent_guidance("CLAUDE.md"))
        write_file(out_dir, "PATH_MAPPING_REFERENCE.md", generate_path_mapping_md())
        write_file(out_dir, "BEGINNER_GUIDE.md", generate_beginner_guide_md(repo_name))
        write_file(out_dir, "ONBOARDING.md", generate_onboarding_md(repo_name))
        write_file(
            out_dir,
            "PROJECTION_SOURCE.json",
            projection_source_record(
                "scripts/publishing/sync_public_repo.py",
                "scripts/publishing/publish_public.py",
            ),
        )
        write_file(out_dir, "scripts/setup_public_workspace.py", generate_public_setup_py())
        for layer in PUBLIC_EXTENSION_LAYERS:
            write_file(out_dir, f"{layer}/README.md", EXTENSION_LAYER_READMES[layer])
        create_required_public_context_dirs(out_dir)
        counts["copied"] += 11

    print()
    if args.dry_run:
        print("DRY RUN complete.")
        return 0

    # Git init
    git_dir = out_dir / ".git"
    for metadata_name in (".gitattributes", ".gitignore"):
        metadata_src = workspace_root / metadata_name
        if metadata_src.is_file():
            shutil.copy2(metadata_src, out_dir / metadata_name)
    if not git_dir.exists():
        try:
            subprocess.run(
                ["git", "init", "-b", "main"],
                cwd=out_dir,
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "add", "."],
                cwd=out_dir,
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "commit", "-m",
                 f"Initial public release: {repo_name}\n\n"
                 "Auto-generated from governed-skill-workspace monorepo.\n"
                 "See PATH_MAPPING_REFERENCE.md for onboarding.\n\n"
                 "Excludes: skills/, agent configs, business code, machine paths."],
                cwd=out_dir,
                capture_output=True,
                check=True,
            )
            counts["git_init"] = 1
        except subprocess.CalledProcessError as exc:
            warnings.append(
                f"Git init failed (stderr): {exc.stderr.decode() if exc.stderr else 'unknown'}"
            )

    print(f"Copied:   {counts.get('copied', 0)} files")
    print(f"Scrubbed: {counts.get('scrubbed', 0)} files")
    print(f"Templated:{counts.get('templated', 0)} files")
    print(f"Stripped: {counts.get('stripped', 0)} skeleton dirs")
    print(f"Git init: {'yes' if counts.get('git_init') else 'already existed'}")
    if warnings:
        print()
        print("Warnings:")
        for w in warnings:
            print(f"  (!) {w}")
    print()
    print(f"Done. Output at: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
