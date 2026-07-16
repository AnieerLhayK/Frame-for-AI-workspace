#!/usr/bin/env python3
"""Regenerate and push the Chatty Ch System public repository.

The remote repository is maintained as a generated artifact. Any checkout made
by this script is disposable staging and is removed after a successful run
unless --keep-staging is supplied for debugging.
"""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

from scripts.workspace.agent_governance import (
    POLICY_PATH,
    check_managed_platform_publish,
    load_manifest,
    load_registry,
    load_yaml,
)
from scripts.workspace.runtime import WORKSPACE_ROOT
PUBLISHER_ID = "chatty_ch_system"
PUBLISHER_SCRIPT = "scripts/sync_chatty_ch_system_repo.py"
DEFAULT_STAGING_ROOT = Path(r"${DATA_ROOT}/codex\cache\staging")
REPO_NAME = "Chatty-Ch-System"
REMOTE_NAME = "origin"
REMOTE_BRANCH = "main"
REMOTE_URL = os.environ.get(
    "CHATTY_CH_REPO_URL",
    "git@github.com:AnieerLhayK/Chatty-Ch-System.git",
)
STAGING_DIR = os.environ.get(
    "CHATTY_CH_STAGING_DIR",
    str(DEFAULT_STAGING_ROOT / REPO_NAME),
)


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def is_managed_staging_path(path: Path) -> bool:
    try:
        path.resolve().relative_to(DEFAULT_STAGING_ROOT.resolve())
    except ValueError:
        return False
    return path.name == REPO_NAME


def cleanup_staging(staging: str, keep_staging: bool = False) -> None:
    staging_path = Path(staging).resolve()
    if keep_staging or not staging_path.exists():
        if keep_staging:
            print(f"[WARN] Kept staging checkout for debugging: {staging_path}")
        return
    if not is_managed_staging_path(staging_path):
        print(f"[WARN] Custom staging path not removed automatically: {staging_path}")
        return

    def remove_readonly(function, path, _exc_info):
        os.chmod(path, stat.S_IWRITE)
        function(path)

    shutil.rmtree(staging_path, onerror=remove_readonly)
    print(f"[OK] Removed disposable staging checkout: {staging_path}")


def workspace_clean() -> bool:
    result = run(["git", "status", "--porcelain"], WORKSPACE_ROOT)
    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        return False
    if result.stdout.strip():
        print("[FAIL] Workspace worktree is dirty; commit or rerun with --force-dirty.", file=sys.stderr)
        print(result.stdout.strip(), file=sys.stderr)
        return False
    return True


def prepare_staging(staging: str, remote_url: str) -> bool:
    path = Path(staging).resolve()
    if not (path / ".git").is_dir():
        if path.exists() and any(path.iterdir()):
            print(f"[FAIL] {path} exists but is not a git repository.", file=sys.stderr)
            return False
        path.parent.mkdir(parents=True, exist_ok=True)
        result = run(["git", "clone", "--branch", REMOTE_BRANCH, remote_url, str(path)], timeout=180)
        if result.returncode != 0:
            print(f"[FAIL] git clone failed: {result.stderr.strip()}", file=sys.stderr)
            return False

    for args in (
        ["remote", "set-url", REMOTE_NAME, remote_url],
        ["fetch", REMOTE_NAME, REMOTE_BRANCH],
        ["checkout", REMOTE_BRANCH],
        ["reset", "--hard", f"{REMOTE_NAME}/{REMOTE_BRANCH}"],
        ["clean", "-fdx"],
        ["rm", "-r", "--ignore-unmatch", "."],
    ):
        result = run(["git", *args], path)
        if result.returncode != 0:
            print(f"[FAIL] git {' '.join(args)} failed: {result.stderr.strip()}", file=sys.stderr)
            return False
    return True


def regenerate(staging: str) -> bool:
    script = WORKSPACE_ROOT / "scripts" / "publish_chatty_ch_system.py"
    result = run([sys.executable, str(script), "--out-dir", staging], WORKSPACE_ROOT, timeout=120)
    output = (result.stdout + result.stderr).strip()
    print(output[-800:])
    return result.returncode == 0


def verify(staging: str, skip_tests: bool = False) -> bool:
    script = WORKSPACE_ROOT / "scripts" / "publish_check_chatty_ch_system.py"
    cmd = [sys.executable, str(script), "--dir", staging]
    if skip_tests:
        cmd.append("--skip-tests")
    result = run(cmd, WORKSPACE_ROOT, timeout=180)
    output = (result.stdout + result.stderr).strip()
    print(output[-1200:])
    return result.returncode == 0


def push(staging: str) -> bool:
    path = Path(staging).resolve()
    status = run(["git", "status", "--porcelain"], path)
    if status.returncode != 0:
        print(status.stderr.strip(), file=sys.stderr)
        return False
    if status.stdout.strip():
        result = run(["git", "add", "-A"], path)
        if result.returncode != 0:
            print(result.stderr.strip(), file=sys.stderr)
            return False
        result = run(["git", "commit", "-m", "sync: regenerate chatty character system"], path)
        if result.returncode != 0:
            print(result.stderr.strip(), file=sys.stderr)
            return False
        print(result.stdout.strip())
    else:
        print("[INFO] No remote changes to commit.")

    result = run(["git", "push", REMOTE_NAME, REMOTE_BRANCH], path, timeout=180)
    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        return False
    print("[OK] Push successful.")
    return True


def require_managed_publish_authorization(
    record_id: str,
    staging: str,
    remote_url: str,
    agent: str,
) -> None:
    authorization = check_managed_platform_publish(
        load_yaml(POLICY_PATH),
        load_manifest(),
        registry=load_registry(),
        publisher_id=PUBLISHER_ID,
        publisher_script=PUBLISHER_SCRIPT,
        agent_name=agent,
        record_id=record_id,
        staging_path=staging,
        remote_url=remote_url,
    )
    if authorization["status"] != "ALLOW":
        raise ValueError(authorization["reason"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync the generated Chatty Ch System public repo.")
    parser.add_argument("--push", action="store_true", help="Push generated changes to the remote.")
    parser.add_argument("--record-id", required=True, help="Active external_write task record.")
    parser.add_argument("--agent", default="codex", help="Registered publishing agent.")
    parser.add_argument("--staging-dir", default=STAGING_DIR, help="Disposable staging checkout.")
    parser.add_argument("--remote-url", default=REMOTE_URL, help="Git remote URL.")
    parser.add_argument("--skip-tests", action="store_true", help="Skip pytest in publish check.")
    parser.add_argument("--force-dirty", action="store_true", help="Allow sync from a dirty workspace.")
    parser.add_argument("--keep-staging", action="store_true", help="Keep staging checkout after successful run.")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        require_managed_publish_authorization(
            args.record_id, args.staging_dir, args.remote_url, args.agent
        )
    except ValueError as error:
        print(f"[FAIL] managed publisher authorization: {error}", file=sys.stderr)
        return 2

    if not args.force_dirty and not workspace_clean():
        return 1
    if not prepare_staging(args.staging_dir, args.remote_url):
        return 1
    if not regenerate(args.staging_dir):
        return 1
    if not verify(args.staging_dir, args.skip_tests):
        return 1
    if args.push and not push(args.staging_dir):
        return 1
    if args.push:
        cleanup_staging(args.staging_dir, args.keep_staging)
    else:
        print("[INFO] Dry run complete; no push requested.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
