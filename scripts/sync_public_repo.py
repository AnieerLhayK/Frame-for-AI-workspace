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
after safe changes (protocol files, scripts, boundary configs). The public
repository is maintained as a remote-only durable artifact; any local clone made
by this script is a disposable staging checkout. By default, the script removes
its managed staging checkout after a successful run so the public repository
does not become a long-lived local deployment.
"""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STAGING_ROOT = Path(
    os.environ.get("AI_TOOL_STAGING_DIR", str(Path(tempfile.gettempdir()) / "ai-workspace-staging"))
)
STAGING_DIR = os.environ.get(
    "PUBLIC_STAGING_DIR",
    str(DEFAULT_STAGING_ROOT / "Frame-for-AI-workspace"),
)
REMOTE_NAME = "origin"
REMOTE_BRANCH = "main"
REMOTE_URL = os.environ.get(
    "PUBLIC_REPO_URL",
    "git@github.com:AnieerLhayK/Frame-for-AI-workspace.git",
)


def _is_managed_staging_path(staging_path: Path) -> bool:
    """Return True only for the script-managed disposable staging checkout."""
    try:
        staging_path.resolve().relative_to(DEFAULT_STAGING_ROOT.resolve())
    except ValueError:
        return False
    return staging_path.name == "Frame-for-AI-workspace"


def cleanup_staging(staging: str, keep_staging: bool = False) -> None:
    """Remove the script-managed staging checkout after successful work."""
    staging_path = Path(staging).resolve()
    if keep_staging:
        print("[WARN] Keeping staging checkout for temporary debugging only.")
        print("       Delete it after inspection; it is not a maintained local repo.")
        return
    if not staging_path.exists():
        return
    if not _is_managed_staging_path(staging_path):
        print("[WARN] Custom staging path was not removed automatically:")
        print(f"       {staging_path}")
        print("       Remove it manually after use; do not maintain it as a local repo.")
        return
    def remove_readonly(function, path, _exc_info):
        os.chmod(path, stat.S_IWRITE)
        function(path)

    shutil.rmtree(staging_path, onerror=remove_readonly)
    print(f"[OK] Removed disposable staging checkout: {staging_path}")


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


def regenerate(staging: str, repo_name: str = "Frame-for-AI-workspace") -> bool:
    """Run publish_public.py. Return True on success."""
    script = WORKSPACE_ROOT / "scripts" / "publish_public.py"
    if not script.is_file():
        print(f"[FAIL] {script} not found", file=sys.stderr)
        return False

    print(f"[INFO] Regenerating public workspace → {staging}")
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--out-dir",
            staging,
            "--repo-name",
            repo_name,
        ],
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


def run_git(staging_path: Path, args: list[str]) -> subprocess.CompletedProcess:
    """Run git in the staging repository."""
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=staging_path,
    )


def prepare_staging_repo(staging: str, remote_url: str) -> bool:
    """Ensure staging is a clean clone of the public repository."""
    staging_path = Path(staging).resolve()
    if not (staging_path / ".git").is_dir():
        if staging_path.exists() and any(staging_path.iterdir()):
            print(
                f"[FAIL] {staging_path} exists but is not a git repository.",
                file=sys.stderr,
            )
            return False
        staging_path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["git", "clone", "--branch", REMOTE_BRANCH, remote_url, str(staging_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"[FAIL] git clone failed: {result.stderr.strip()}", file=sys.stderr)
            return False

    remote = run_git(staging_path, ["remote", "get-url", REMOTE_NAME])
    if remote.returncode != 0:
        remote = run_git(staging_path, ["remote", "add", REMOTE_NAME, remote_url])
        if remote.returncode != 0:
            print(f"[FAIL] git remote add failed: {remote.stderr.strip()}", file=sys.stderr)
            return False

    for args in (
        ["fetch", REMOTE_NAME, REMOTE_BRANCH],
        ["checkout", REMOTE_BRANCH],
        ["reset", "--hard", f"{REMOTE_NAME}/{REMOTE_BRANCH}"],
        ["clean", "-fdx"],
        ["rm", "-r", "--ignore-unmatch", "."],
    ):
        result = run_git(staging_path, args)
        if result.returncode != 0:
            print(
                f"[FAIL] git {' '.join(args)} failed: {result.stderr.strip()}",
                file=sys.stderr,
            )
            return False
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
        "--remote-url", default=REMOTE_URL,
        help=f"Public repository URL (default: {REMOTE_URL})",
    )
    parser.add_argument(
        "--force-dirty", action="store_true",
        help="Allow sync even with uncommitted workspace changes.",
    )
    parser.add_argument(
        "--keep-staging", action="store_true",
        help=(
            "Temporarily keep the staging checkout for debugging. This is not "
            "a local deployment and must be deleted after inspection."
        ),
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
    if args.push and not prepare_staging_repo(args.staging_dir, args.remote_url):
        return 1
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
    cleanup_staging(args.staging_dir, keep_staging=args.keep_staging)
    print()

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
