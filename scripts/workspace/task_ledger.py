#!/usr/bin/env python3
"""Losslessly migrate and validate a day-partitioned task ledger."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from scripts.workspace.project_context import TASK_LEDGER_ROOT
from scripts.workspace.runtime import WORKSPACE_ROOT
DESTINATION = TASK_LEDGER_ROOT
MIGRATION_RECEIPT = DESTINATION / "migration_receipt.yaml"
LEGACY_DIRECTORY = DESTINATION / "legacy"
ENTRY = re.compile(r"(?=^### TASK-)", re.MULTILINE)
DATE = re.compile(r"^- Date: (\d{4})-(\d{2})-(\d{2})\s*$", re.MULTILINE)
TASK_HEADING = re.compile(r"^### (TASK-[^\s]+)\b", re.MULTILINE)

def entries(text: str) -> list[str]:
    positions = [match.start() for match in ENTRY.finditer(text)]
    return [text[start:end] for start, end in zip(positions, positions[1:] + [len(text)])]

def write_day(target: Path, items: list[str]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# Task Ledger\n\n" + "\n\n".join(items).rstrip() + "\n", encoding="utf-8")


def record_day(record: dict[str, Any]) -> dt.date:
    """Keep the human ledger partition aligned with task-record storage."""
    value = str(record["started_at"]).replace("Z", "+00:00")
    return dt.datetime.fromisoformat(value).date()


def record_entry(record: dict[str, Any], record_path: Path) -> str:
    """Render a compact, machine-derived ledger entry for one finalized record."""
    task_id = str(record["task_id"])
    task_type = str(record.get("task_type") or "workspace_task")
    title = task_type.replace("_", " ")
    registration = record.get("registration", {})
    operations = registration.get("operations", []) if isinstance(registration, dict) else []
    validation = record.get("validation", {})
    commands = validation.get("commands", []) if isinstance(validation, dict) else []
    try:
        display_path = record_path.relative_to(WORKSPACE_ROOT).as_posix()
    except ValueError:
        display_path = record_path.as_posix()

    lines = [
        f"### {task_id} - {title}",
        "",
        f"- Date: {record_day(record).isoformat()}",
        "- Origin: automatic task-outcome record synchronization",
        f"- Task type: {task_type}",
        f"- Outcome: {record.get('status', 'unknown')}",
        f"- Validation: {validation.get('status', 'unknown')}",
        f"- Usability: {record.get('usability', {}).get('status', 'unknown')}",
        f"- Operations: {', '.join(operations) if operations else 'not recorded'}",
        f"- Task record: `{display_path}`",
    ]
    if commands:
        lines.append("- Validation commands:")
        lines.extend(f"  - `{command}`" for command in commands)
    return "\n".join(lines)


def upsert_task_record(record_path: Path, record: dict[str, Any]) -> bool:
    """Append one finalized task record to its day ledger without duplicates."""
    if record.get("status") == "in_progress":
        return False

    day = record_day(record)
    target = DESTINATION / f"{day:%Y}" / f"{day:%m}" / f"{day:%d}.md"
    existing = target.read_text(encoding="utf-8") if target.is_file() else "# Task Ledger\n"
    known_ids = set(TASK_HEADING.findall(existing))
    if str(record["task_id"]) in known_ids:
        return False

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        existing.rstrip() + "\n\n" + record_entry(record, record_path) + "\n",
        encoding="utf-8",
    )
    return True

def partition() -> None:
    for monthly in DESTINATION.glob("20??/??.md"):
        grouped: dict[str, list[str]] = defaultdict(list)
        for entry in entries(monthly.read_text(encoding="utf-8")):
            match = DATE.search(entry)
            if not match: raise ValueError(f"Undated entry in {monthly}")
            grouped[match.group(3)].append(entry)
        for day, items in grouped.items(): write_day(monthly.parent / monthly.stem / f"{day}.md", items)
        monthly.unlink()

def _daily_task_ids() -> set[str]:
    archived = list(DESTINATION.glob("20??/??/??.md"))
    task_ids: set[str] = set()
    for path in archived:
        task_ids.update(TASK_HEADING.findall(path.read_text(encoding="utf-8")))
    return task_ids


def git_blob_matches(receipt: dict[str, Any]) -> bool | None:
    """Return whether the recorded source blob matches, or None outside Git."""
    inside = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=WORKSPACE_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return None
    blob = str(receipt.get("source_blob", ""))
    expected_hash = str(receipt.get("source_sha256", ""))
    result = subprocess.run(
        ["git", "cat-file", "blob", blob],
        cwd=WORKSPACE_ROOT,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0 and hashlib.sha256(result.stdout).hexdigest().upper() == expected_hash.upper()


def validate() -> bool:
    if LEGACY_DIRECTORY.is_dir() and any(LEGACY_DIRECTORY.iterdir()):
        return False
    if not MIGRATION_RECEIPT.is_file():
        return False
    try:
        receipt = yaml.safe_load(MIGRATION_RECEIPT.read_text(encoding="utf-8-sig"))
    except (OSError, yaml.YAMLError):
        return False
    if not isinstance(receipt, dict) or receipt.get("schema_version") != "1.0":
        return False
    task_ids = receipt.get("task_ids")
    if not isinstance(task_ids, list) or not task_ids or not all(isinstance(item, str) for item in task_ids):
        return False
    if not {"source_commit", "source_blob", "source_sha256", "source_path"} <= set(receipt):
        return False
    if not set(task_ids) <= _daily_task_ids():
        return False
    blob_status = git_blob_matches(receipt)
    return blob_status is not False

def sync_records(*, task_id: str | None = None, day: str | None = None) -> list[str]:
    """Backfill finalized task records, optionally for one task or one day."""
    from scripts.workspace import task_records

    target_day = dt.date.fromisoformat(day) if day else None
    synced: list[str] = []
    for path in sorted(task_records.RECORD_ROOT.glob("*/*/*/TASK-*.json")):
        record_path, record = task_records.read_record(path.stem)
        if task_id and record["task_id"] != task_id:
            continue
        if target_day and record_day(record) != target_day:
            continue
        if upsert_task_record(record_path, record):
            synced.append(record["task_id"])
    return synced


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("partition")
    sub.add_parser("validate")
    sync = sub.add_parser("sync-records")
    sync.add_argument("--task-id")
    sync.add_argument("--date", help="ISO date (YYYY-MM-DD) for backfill")
    args = parser.parse_args()
    if args.action == "partition":
        partition()
        return 0
    if args.action == "sync-records":
        print("\n".join(sync_records(task_id=args.task_id, day=args.date)))
        return 0
    print("PASS" if validate() else "FAIL")
    return 0 if validate() else 1

if __name__ == "__main__": raise SystemExit(main())
