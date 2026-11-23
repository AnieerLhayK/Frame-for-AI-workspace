"""Narrow Git cleanliness checks for registered public publishers."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


TASK_ID = re.compile(r"^TASK-(\d{4})(\d{2})(\d{2})-\d{3}$")


def task_record_path(record_id: str) -> str | None:
    """Return the canonical record path encoded by a valid task id."""
    match = TASK_ID.fullmatch(record_id)
    if not match:
        return None
    year, month, day = match.groups()
    return f"PROJECT_CONTEXT/tasks/records/{year}/{month}/{day}/{record_id}.json"


def workspace_clean_for_record(workspace_root: Path, record_id: str) -> bool:
    """Allow a clean tree or only the exact active record as unstaged dirt."""
    expected = task_record_path(record_id)
    if expected is None:
        return False
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=workspace_root,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        return False
    entries = [entry for entry in result.stdout.split("\0") if entry]
    if not entries:
        return True
    for entry in entries:
        if len(entry) < 4 or entry[2] != " ":
            return False
        status = entry[:2]
        path = entry[3:].replace("\\", "/")
        if status not in {"??", " M"} or path != expected:
            return False
    return True
