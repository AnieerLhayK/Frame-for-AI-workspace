#!/usr/bin/env python3
"""sync_public_repo.py — Regenerate and push public workspace skeleton.

Usage:
    python scripts/sync_public_repo.py                              # dry-run
    python scripts/sync_public_repo.py --dry-run                    # explicit dry-run
    python scripts/sync_public_repo.py --push                       # regenerate + push

Workflow:
    1. Check that the local workspace is clean (no uncommitted changes).
    2. Run publish_public.py to regenerate the staging directory.
    3. Run publish_check.py to verify the staging directory.
    4. If --push and all checks pass, git commit + push to remote.
    5. Print a summary of what was updated.

Use this script to keep the public skeleton in sync with the private workspace
after safe changes (protocol files, scripts, boundary configs).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
STAGING_DIR = os.environ.get(
    "PUBLIC_STAGING_DIR",
    str(WORKSPACE_ROOT / "publish-staging"),
)
REMOTE_NAME = "origin"
REMOTE_BRANCH = "main"


def check_workspace_clean() -> bool:
    """Return True if the workspace git tree is clean."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=WORKSPACE_ROOT,
    )
    if result.returncode != 0:
        print("[FAIL] Cannot check git status — not a git repository?", file=sys.stderr)
        return False
    if result.stdout.strip():
        print("[WARN] Workspace has uncommitted changes:", file=sys.stderr)
        for line in result.stdout.strip().split("\n"):
            print(f"       {line}", file=sys.stderr)
        print(file=sys.stderr)
        return False
    return True


def regenerate(staging: str) -> bool:
    """Run publish_public.py. Return True on success."""
    script = WORKSPACE_ROOT / "scripts" / "publish_public.py"
    if not script.is_file():
        print(f"[FAIL] {script} not found", file=sys.stderr)
        return False

    print(f"[INFO] Regenerating public workspace → {staging}")
    result = subprocess.run(
        [sys.executable, str(script), "--out-dir", staging],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        print(f"[FAIL] publish_public.py exited {result.returncode}", file=sys.stderr)
        print(result.stderr.strip()[-500:], file=sys.stderr)
        return False

    # Print last line of output (the summary)
    summary = [l for l in result.stdout.strip().split("\n") if l.strip()][-3:]
    for l in summary:
        print(f"  {l}")
    return True


def verify(staging: str, skip_tests: bool = False) -> bool:
    """Run publish_check.py. Return True on success."""
    script = WORKSPACE_ROOT / "scripts" / "publish_check.py"
    if not script.is_file():
        print(f"[FAIL] {script} not found", file=sys.stderr)
        return False

    cmd = [sys.executable, str(script), "--dir", staging]
    if skip_tests:
        cmd.append("--skip-tests")
        cmd.append("--skip-functional")

    print("[INFO] Verifying staging directory ...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    output = (result.stdout + result.stderr).strip()
    print(output[-600:])  # tail of output

    return result.returncode == 0


def push_to_remote(staging: str) -> bool:
    """Commit (if dirty) and push the staging repo. Return True on success."""
    staging_path = Path(staging)
    if not (staging_path / ".git").is_dir():
        print(f"[FAIL] {staging} is not a git repository", file=sys.stderr)
        return False

    # Check if there are changes to commit
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=staging_path,
    )
    has_changes = bool(result.stdout.strip())

    if has_changes:
        result = subprocess.run(
            ["git", "add", "-A"],
            capture_output=True, text=True, cwd=staging_path,
        )
        if result.returncode != 0:
            print(f"[FAIL] git add failed: {result.stderr.strip()}", file=sys.stderr)
            return False

        result = subprocess.run(
            ["git", "commit", "-m", "sync: regenerate public workspace skeleton"],
            capture_output=True, text=True, cwd=staging_path,
        )
        if result.returncode != 0:
            print(f"[FAIL] git commit failed: {result.stderr.strip()}", file=sys.stderr)
            return False
        print(f"[INFO] Commit: {result.stdout.strip()}")
    else:
        print("[INFO] No changes — nothing to commit.")

    result = subprocess.run(
        ["git", "push", REMOTE_NAME, REMOTE_BRANCH],
        capture_output=True, text=True, cwd=staging_path,
    )
    if result.returncode != 0:
        print(f"[FAIL] git push failed: {result.stderr.strip()}", file=sys.stderr)
        return False

    print(f"[OK] Push successful ({REMOTE_NAME}/{REMOTE_BRANCH}).")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate and push the public workspace skeleton repo."
    )
    parser.add_argument(
        "--push", action="store_true",
        help="Actually push to remote (default: dry-run only).",
    )
    parser.add_argument(
        "--dry-run", action="store_true", dest="dry_run",
        help="Explicit dry-run (check + regenerate + verify, no push).",
    )
    parser.add_argument(
        "--skip-tests", action="store_true",
        help="Skip pytest in verification (faster).",
    )
    parser.add_argument(
        "--staging-dir", default=STAGING_DIR,
        help=f"Staging directory (default: {STAGING_DIR})",
    )
    parser.add_argument(
        "--force-dirty", action="store_true",
        help="Allow sync even with uncommitted workspace changes.",
    )
    args = parser.parse_args()

    print("=" * 54)
    print("  Public Workspace Sync")
    print("=" * 54)
    print()

    # Step 1: Clean workspace check
    print("[1/5] Checking workspace git status ...")
    if not args.force_dirty and not check_workspace_clean():
        print("[ABORT] Workspace has uncommitted changes.", file=sys.stderr)
        print("        Commit or stash them first, or use --force-dirty.", file=sys.stderr)
        return 1
    print("  [OK]")
    print()

    # Step 2: Current branch info
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True, text=True, cwd=WORKSPACE_ROOT,
    ).stdout.strip()
    merge_base = subprocess.run(
        ["git", "merge-base", "HEAD", "main"],
        capture_output=True, text=True, cwd=WORKSPACE_ROOT,
    ).stdout.strip()[:8]
    print(f"[2/5] Current branch: {branch} (merge-base: {merge_base})")
    print()

    # Step 3: Regenerate
    print("[3/5] Regenerating staging directory ...")
    if not regenerate(args.staging_dir):
        return 1
    print()

    # Step 4: Verify
    print("[4/5] Verifying staging directory ...")
    if not verify(args.staging_dir, skip_tests=args.skip_tests):
        print("[ABORT] Verification failed.", file=sys.stderr)
        return 1
    print()

    # Step 5: Push
    print("[5/5] Publishing ...")
    if args.push:
        if not push_to_remote(args.staging_dir):
            return 1
    else:
        print("  [DRY-RUN] Use --push to actually push to remote.")
        print(f"  Staging dir: {args.staging_dir}")
        print(f"  Remote:      {REMOTE_NAME} {REMOTE_BRANCH}")
    print()

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
