#!/usr/bin/env python3
"""sync_public_repo.py — Regenerate and push public workspace skeleton.

Usage:
    python -m scripts.publishing.sync_public_repo                              # dry-run
    python -m scripts.publishing.sync_public_repo --dry-run                    # explicit dry-run
    python -m scripts.publishing.sync_public_repo --push                       # regenerate + push

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
import subprocess
import sys
from pathlib import Path

from scripts.workspace.runtime import WORKSPACE_ROOT
from scripts.publishing.workspace_state import workspace_clean_for_record
from scripts.publishing import registered_repo_sync
PUBLISHER_ID = "frame_for_ai_workspace"
PUBLISHER_SCRIPT = "scripts/publishing/sync_public_repo.py"
DEFAULT_STAGING_ROOT = Path(r"${DATA_ROOT}/codex\cache\staging")
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
    return registered_repo_sync.is_managed_staging_path(
        staging_path, DEFAULT_STAGING_ROOT, "Frame-for-AI-workspace"
    )


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
    if registered_repo_sync.cleanup_staging(
        staging_path, DEFAULT_STAGING_ROOT / "Frame-for-AI-workspace"
    ):
        print(f"[OK] Removed disposable staging checkout: {staging_path}")


def check_workspace_clean(record_id: str) -> bool:
    """Allow no dirt except the exact active task-record path."""
    return workspace_clean_for_record(WORKSPACE_ROOT, record_id)


def regenerate(staging: str, repo_name: str = "Frame-for-AI-workspace") -> bool:
    """Run publish_public.py. Return True on success."""
    print(f"[INFO] Regenerating public workspace → {staging}")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.publishing.publish_public",
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
    try:
        registered_repo_sync.prepare_staging(Path(staging), remote_url, REMOTE_BRANCH)
    except RuntimeError as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        return False
    return True


def verify(staging: str, skip_tests: bool = False) -> bool:
    """Run publish_check.py. Return True on success."""
    cmd = [sys.executable, "-m", "scripts.publishing.publish_check", "--dir", staging]
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
    try:
        registered_repo_sync.commit_and_push(
            Path(staging), "sync: regenerate public workspace skeleton", REMOTE_BRANCH
        )
    except RuntimeError as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        return False
    print(f"[OK] Push successful ({REMOTE_NAME}/{REMOTE_BRANCH}).")
    return True


def require_managed_publish_authorization(
    record_id: str,
    staging: str,
    remote_url: str,
    agent: str,
) -> None:
    registered_repo_sync.require_managed_publish_authorization(
        publisher_id=PUBLISHER_ID,
        publisher_script=PUBLISHER_SCRIPT,
        record_id=record_id,
        staging_path=staging,
        remote_url=remote_url,
        agent=agent,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Regenerate and push the public workspace skeleton repo."
    )
    parser.add_argument(
        "--push", action="store_true",
        help="Actually push to remote (default: dry-run only).",
    )
    parser.add_argument(
        "--preview", action="store_true",
        help="Preview generated files on a temporary branch in the registered remote, then delete it.",
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
    parser.add_argument("--record-id", required=True, help="Active external_write task record.")
    parser.add_argument("--agent", default="codex", help="Registered publishing agent.")
    parser.add_argument(
        "--force-dirty", action="store_true",
        help="Allow a preview from an uncommitted workspace.",
    )
    parser.add_argument(
        "--keep-staging", action="store_true",
        help=(
            "Temporarily keep the staging checkout for debugging. This is not "
            "a local deployment and must be deleted after inspection."
        ),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.push and args.preview:
        raise SystemExit("--push and --preview are mutually exclusive")
    if args.force_dirty and not args.preview:
        raise SystemExit("--force-dirty is available only for a preview")

    try:
        require_managed_publish_authorization(
            args.record_id, args.staging_dir, args.remote_url, args.agent
        )
    except ValueError as error:
        print(f"[FAIL] managed publisher authorization: {error}", file=sys.stderr)
        return 2

    print("=" * 54)
    print("  Public Workspace Sync")
    print("=" * 54)
    print()

    # Step 1: Clean workspace check
    print("[1/5] Checking workspace git status ...")
    if not args.force_dirty and not check_workspace_clean(args.record_id):
        print("[ABORT] Workspace has uncommitted changes.", file=sys.stderr)
        print("        Commit or stash them first, or use --force-dirty with --preview.", file=sys.stderr)
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
    # Dry-runs must start from the registered remote baseline too. Otherwise a
    # previous failed run can leave tracked files in the managed staging clone,
    # and the generator only overwrites selected paths instead of removing
    # stale public content.
    if not prepare_staging_repo(args.staging_dir, args.remote_url):
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
    if args.preview:
        try:
            registered_repo_sync.preview_staging_remotely(
                Path(args.staging_dir), "preview: regenerate public workspace skeleton"
            )
        except (RuntimeError, ValueError) as error:
            print(f"[ABORT] Preview failed: {error}", file=sys.stderr)
            return 1
        print("[OK] Remote preview inspected and temporary branch deleted.")
    elif args.push:
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
