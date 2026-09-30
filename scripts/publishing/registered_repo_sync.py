"""Shared mechanics for registered, generated GitHub projections."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import uuid
from pathlib import Path

def run_git(command: list[str], cwd: Path | None = None, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def is_managed_staging_path(path: Path, root: Path, checkout_name: str) -> bool:
    try:
        resolved, expected_root = path.resolve(), root.resolve()
        resolved.relative_to(expected_root)
    except ValueError:
        return False
    return resolved.parent == expected_root and resolved.name == checkout_name


def cleanup_staging(staging: Path, managed_path: Path, keep: bool = False) -> bool:
    path = staging.resolve()
    if keep or not path.exists():
        return True
    if path != managed_path.resolve():
        print(f"[WARN] Custom staging path was not removed automatically: {path}")
        return False

    def remove_readonly(function, filename, _exc_info):
        os.chmod(filename, stat.S_IWRITE)
        function(filename)

    try:
        shutil.rmtree(path, onerror=remove_readonly)
    except OSError as exc:
        print(f"[WARN] Staging cleanup failed: {exc}")
        return False
    return True


def prepare_staging(staging: Path, remote_url: str, branch: str = "main") -> None:
    """Reset an authorized disposable checkout to its remote baseline and empty the tree."""
    path = staging.resolve()
    if not (path / ".git").is_dir():
        if path.exists() and any(path.iterdir()):
            raise RuntimeError(f"staging path is not an empty git checkout: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        result = run_git(["git", "clone", "--branch", branch, remote_url, str(path)], timeout=240)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or "git clone failed")

    remote = run_git(["git", "remote", "get-url", "origin"], path)
    command = (
        ["git", "remote", "set-url", "origin", remote_url]
        if remote.returncode == 0
        else ["git", "remote", "add", "origin", remote_url]
    )
    result = run_git(command, path)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"failed: {' '.join(command)}")

    for command in (
        ["git", "fetch", "origin", branch],
        ["git", "checkout", branch],
        ["git", "reset", "--hard", f"origin/{branch}"],
        ["git", "clean", "-fdx"],
        ["git", "rm", "-r", "--ignore-unmatch", "."],
    ):
        result = run_git(command, path)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or f"failed: {' '.join(command)}")


def commit_and_push(staging: Path, message: str, branch: str = "main") -> None:
    path = staging.resolve()
    if not (path / ".git").is_dir():
        raise RuntimeError(f"{path} is not a git repository")
    commit_changes(path, message)
    result = run_git(["git", "push", "origin", branch], path, timeout=240)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git push failed")


def commit_changes(staging: Path, message: str) -> None:
    """Commit all generated staging changes without selecting a remote target."""
    path = staging.resolve()
    if not (path / ".git").is_dir():
        raise RuntimeError(f"{path} is not a git repository")
    status = run_git(["git", "status", "--porcelain"], path)
    if status.returncode:
        raise RuntimeError(status.stderr.strip() or "git status failed")
    if status.stdout.strip():
        result = run_git(["git", "add", "-A"], path)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or "git add failed")
        staged = run_git(["git", "status", "--porcelain"], path)
        if staged.returncode:
            raise RuntimeError(staged.stderr.strip() or "git status failed")
        if staged.stdout.strip():
            result = run_git(["git", "commit", "-m", message], path)
            if result.returncode:
                raise RuntimeError(result.stderr.strip() or "git commit failed")


def require_managed_publish_authorization(
    *, publisher_id: str, publisher_script: str, record_id: str,
    staging_path: str, remote_url: str, agent: str,
) -> None:
    from scripts.workspace.agent_governance import (
        POLICY_PATH, check_managed_platform_publish, load_manifest, load_registry, load_yaml,
    )

    result = check_managed_platform_publish(
        load_yaml(POLICY_PATH), load_manifest(), registry=load_registry(),
        publisher_id=publisher_id, publisher_script=publisher_script,
        agent_name=agent, record_id=record_id,
        staging_path=staging_path, remote_url=remote_url,
    )
    if result["status"] != "ALLOW":
        raise ValueError(result["reason"])


def preview_staging_remotely(staging: Path, message: str) -> str:
    """Push generated staging to a unique temporary remote branch, then delete it."""
    if not sys.stdin.isatty():
        raise RuntimeError("remote preview requires an interactive terminal")

    path = staging.resolve()
    remote = run_git(["git", "remote", "get-url", "origin"], path)
    if remote.returncode or not remote.stdout.strip():
        raise RuntimeError(remote.stderr.strip() or "staging checkout has no origin remote")

    branch = f"codex-preview/{uuid.uuid4().hex}"
    refs = run_git(["git", "ls-remote", "--heads", "origin", f"refs/heads/{branch}"], path)
    if refs.returncode:
        raise RuntimeError(refs.stderr.strip() or "could not check temporary preview branch")
    if refs.stdout.strip():
        raise RuntimeError(f"temporary preview branch already exists: {branch}")

    published_head: str | None = None
    created = False
    try:
        commit_changes(path, message)
        head = run_git(["git", "rev-parse", "HEAD"], path)
        if head.returncode or not head.stdout.strip():
            raise RuntimeError(head.stderr.strip() or "could not resolve preview commit")
        published_head = head.stdout.strip()
        push_error: str | None = None
        try:
            pushed = run_git(
                [
                    "git", "push", f"--force-with-lease=refs/heads/{branch}:",
                    "origin", f"{published_head}:refs/heads/{branch}",
                ],
                path,
                timeout=240,
            )
            if pushed.returncode:
                push_error = pushed.stderr.strip() or "temporary preview push failed"
        except subprocess.TimeoutExpired:
            push_error = "temporary preview push timed out"

        pushed_ref = run_git(
            ["git", "ls-remote", "--heads", "origin", f"refs/heads/{branch}"], path
        )
        if pushed_ref.returncode:
            cleanup = run_git(
                [
                    "git", "push", f"--force-with-lease=refs/heads/{branch}:{published_head}",
                    "origin", f":refs/heads/{branch}",
                ],
                path,
                timeout=240,
            )
            if cleanup.returncode:
                print(
                    f"[WARN] Preview branch state is unknown and guarded cleanup failed; inspect remote ref: {branch}",
                    file=sys.stderr,
                )
            else:
                print(f"[INFO] Removed preview branch after ambiguous push result: {branch}")
            raise RuntimeError(pushed_ref.stderr.strip() or "could not verify temporary preview branch")
        remote_head = pushed_ref.stdout.split(maxsplit=1)[0] if pushed_ref.stdout.strip() else None
        created = remote_head == published_head
        if not created:
            if remote_head:
                print(
                    f"[WARN] Preview branch moved to another revision and was left untouched; inspect ref: {branch}",
                    file=sys.stderr,
                )
            raise RuntimeError(push_error or "temporary preview branch was not created at the expected revision")
        print(f"[PREVIEW] Inspect registered remote branch: {branch}")
        input("Press Enter after inspecting the preview; the temporary branch will be deleted. ")
        return branch
    finally:
        if created and published_head:
            deleted = run_git(
                [
                    "git", "push", f"--force-with-lease=refs/heads/{branch}:{published_head}",
                    "origin", f":refs/heads/{branch}",
                ],
                path,
                timeout=240,
            )
            if deleted.returncode:
                print(
                    f"[WARN] Temporary preview branch may remain; inspect and clean up if it still points to {published_head}: {branch}",
                    file=sys.stderr,
                )
                raise RuntimeError(
                    deleted.stderr.strip()
                    or f"temporary preview branch could not be safely deleted: {branch}"
                )
