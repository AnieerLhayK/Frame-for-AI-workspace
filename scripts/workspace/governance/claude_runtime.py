"""Claude's session-to-TASK adapter and finite post-finalization shell gate."""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shlex
from pathlib import Path

from scripts.workspace import task_records
from scripts.workspace.agent_governance import require_task_actor
from scripts.workspace.merge_safety import audit_worktree_scope, git


def session_record(session_id: str, explicit: str | None = None) -> str:
    if explicit:
        _, record = task_records.read_record(explicit)
        candidates = [record]
    else:
        if not session_id:
            raise ValueError("Claude session_id is required to discover its TASK")
        candidates = [r for r in task_records.records()
                      if r.get("owner", {}).get("agent") == "claude"
                      and r.get("owner", {}).get("session_id") == session_id
                      and r.get("status") in {"in_progress", "successful"}]
        candidates.sort(key=lambda r: (r["status"] == "in_progress", r["started_at"], r["task_id"]), reverse=True)
    if not candidates:
        raise ValueError("start an owned Claude TASK with --owner-session matching this session")
    record = candidates[0]
    owner = record.get("owner", {})
    if owner.get("agent") != "claude" or (session_id and owner.get("session_id") != session_id):
        raise ValueError("TASK owner or session does not match Claude")
    return record["task_id"]


def check_shell(record_id: str, command: str) -> None:
    _, record = task_records.read_record(record_id)
    words = [part.strip('\"\'') for part in shlex.split(command, posix=False)]
    if words[:2] == ["git", "-C"]:
        if len(words) < 4 or words[3:] != ["merge", "--ff-only", "dev"]:
            raise ValueError("git -C delivery is limited to main-worktree ff-only integration")
        requested = str(Path(words[2]).resolve()).casefold()
        registered = []
        for block in git("worktree", "list", "--porcelain").split("\n\n"):
            rows = block.splitlines()
            if "branch refs/heads/main" in rows:
                registered.extend(str(Path(row.removeprefix("worktree ")).resolve()).casefold()
                                  for row in rows if row.startswith("worktree "))
        if requested not in registered:
            raise ValueError("integration target is not a registered main worktree")
        if git("-C", words[2], "status", "--porcelain"):
            raise ValueError("main integration worktree must be clean")
        words = ["git", *words[3:]]
    if record.get("status") == "in_progress":
        require_task_actor(record_id, "claude", "workspace_write")
        return
    # Shell interpreters and compounds are not audit actions. Inspect the
    # actual tree too: naming an audit command cannot authorize source edits.
    if re.search(r"[;&|<>`\r\n]", command):
        raise ValueError("finalized TASK permits only a single audit-close command")
    git_action = len(words) > 1 and words[0] == "git" and words[1] in {"add", "commit", "merge", "push"}
    fetch = words == ["git", "fetch", "origin"]
    preflight = (words[:3] == ["workspace", "merge", "main"]
                 and "--record-id" in words and words[words.index("--record-id") + 1:] == [record_id])
    review = (words[:3] == ["workspace", "records", "note-merge-review"]
              and len(words) > 3 and words[3] == record_id and "--audit-close" in words)
    if not git_action and not review and not fetch and not preflight:
        raise ValueError("finalized TASK permits only audit staging, commit, review, preflight, fetch, merge and push")
    audit_worktree_scope(record_id, allow_integrated=words[:2] == ["git", "push"] or fetch)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-id", default="")
    parser.add_argument("--record-id")
    parser.add_argument("--shell-command-base64")
    args = parser.parse_args()
    try:
        record_id = session_record(args.session_id, args.record_id or os.environ.get("WORKSPACE_TASK_RECORD"))
        if args.shell_command_base64 is not None:
            command = base64.b64decode(args.shell_command_base64, validate=True).decode("utf-8")
            check_shell(record_id, command)
        print(record_id)
        return 0
    except (ValueError, OSError) as error:
        print(json.dumps({"error": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
