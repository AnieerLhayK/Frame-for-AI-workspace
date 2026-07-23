#!/usr/bin/env python3
"""Synchronize every registered public projection through its own publisher.

The publisher registry in ``shared/agent_governance.yaml`` is the sole list of
public repositories.  Adding a managed publisher there makes it part of this
command without adding another hand-maintained dispatch table.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Sequence

from scripts.workspace.agent_governance import POLICY_PATH, load_yaml
from scripts.workspace.runtime import WORKSPACE_ROOT


def registered_publishers(policy: dict[str, Any]) -> dict[str, str]:
    """Return publisher ids and their registered workspace-relative scripts."""
    publishers = policy.get("managed_platform_publishers", {})
    if not isinstance(publishers, dict):
        raise ValueError("managed_platform_publishers must be a mapping")

    result: dict[str, str] = {}
    for publisher_id, publisher in publishers.items():
        if not isinstance(publisher, dict):
            raise ValueError(f"publisher {publisher_id!r} must be a mapping")
        script = str(publisher.get("publisher_script", "")).replace("\\", "/")
        if not script.startswith("scripts/") or not script.endswith(".py"):
            raise ValueError(f"publisher {publisher_id!r} has an invalid publisher_script")
        script_path = (WORKSPACE_ROOT / script).resolve()
        if not script_path.is_file() or WORKSPACE_ROOT not in script_path.parents:
            raise ValueError(f"publisher {publisher_id!r} script is unavailable: {script}")
        result[str(publisher_id)] = script
    return result


def integrated_main_error(
    head: str | None, main: str | None, remote_main: str | None
) -> str | None:
    """Return why a push is not sourced from the current integrated main."""
    if not head or not main:
        return "cannot resolve both HEAD and refs/heads/main"
    if head != main:
        return "publication requires HEAD to equal refs/heads/main"
    if not remote_main:
        return "cannot resolve refs/remotes/origin/main"
    if main != remote_main:
        return "publication requires local main to equal origin/main"
    return None


def git_ref(ref: str) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", ref],
        cwd=WORKSPACE_ROOT,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def build_parser(publisher_ids: Sequence[str]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Regenerate and verify all registered public projections."
    )
    parser.add_argument("--record-id", required=True, help="Active external_write task record.")
    parser.add_argument("--agent", default="codex", help="Registered publishing agent.")
    parser.add_argument(
        "--publisher",
        action="append",
        choices=publisher_ids,
        help="Synchronize only this registered publisher; repeat to select several.",
    )
    parser.add_argument("--push", action="store_true", help="Commit and push each generated projection.")
    parser.add_argument("--skip-tests", action="store_true", help="Pass the publisher's fast verification option.")
    return parser


def publisher_command(
    script: str, *, record_id: str, agent: str, push: bool, skip_tests: bool
) -> list[str]:
    command = [sys.executable, str(WORKSPACE_ROOT / script), "--record-id", record_id, "--agent", agent]
    if skip_tests:
        command.append("--skip-tests")
    if push:
        command.append("--push")
    return command


def sync_publishers(
    publishers: dict[str, str],
    selected: Sequence[str],
    *,
    record_id: str,
    agent: str,
    push: bool,
    skip_tests: bool,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> int:
    """Run the selected publishers in a deterministic order; stop on failure."""
    targets = list(selected) if selected else sorted(publishers)
    for publisher_id in targets:
        command = publisher_command(
            publishers[publisher_id],
            record_id=record_id,
            agent=agent,
            push=push,
            skip_tests=skip_tests,
        )
        print(f"[INFO] {publisher_id}: {' '.join(command)}")
        result = runner(command, cwd=WORKSPACE_ROOT, text=True)
        if result.returncode != 0:
            print(f"[FAIL] {publisher_id} exited {result.returncode}", file=sys.stderr)
            return result.returncode or 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    try:
        publishers = registered_publishers(load_yaml(POLICY_PATH))
    except ValueError as error:
        print(f"[FAIL] public projection registry: {error}", file=sys.stderr)
        return 2
    if not publishers:
        print("[FAIL] public projection registry is empty", file=sys.stderr)
        return 2

    args = build_parser(sorted(publishers)).parse_args(argv)
    if args.push:
        error = integrated_main_error(
            git_ref("HEAD"), git_ref("refs/heads/main"), git_ref("refs/remotes/origin/main")
        )
        if error:
            print(f"[FAIL] public projection source revision: {error}", file=sys.stderr)
            return 2
    mode = "push" if args.push else "dry-run"
    print(f"[INFO] Public projection synchronization ({mode})")
    return sync_publishers(
        publishers,
        args.publisher or [],
        record_id=args.record_id,
        agent=args.agent,
        push=args.push,
        skip_tests=args.skip_tests,
    )


if __name__ == "__main__":
    raise SystemExit(main())
