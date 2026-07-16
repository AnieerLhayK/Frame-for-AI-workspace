#!/usr/bin/env python3
"""Losslessly migrate and validate a day-partitioned task ledger."""
from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "PROJECT_CONTEXT" / "task_ledger.md"
DESTINATION = ROOT / "PROJECT_CONTEXT" / "task_ledger"
ENTRY = re.compile(r"(?=^### TASK-)", re.MULTILINE)
DATE = re.compile(r"^- Date: (\d{4})-(\d{2})-(\d{2})\s*$", re.MULTILINE)

def entries(text: str) -> list[str]:
    positions = [match.start() for match in ENTRY.finditer(text)]
    return [text[start:end] for start, end in zip(positions, positions[1:] + [len(text)])]

def write_day(target: Path, items: list[str]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# Task Ledger\n\n" + "\n\n".join(items).rstrip() + "\n", encoding="utf-8")

def partition() -> None:
    for monthly in DESTINATION.glob("20??/??.md"):
        grouped: dict[str, list[str]] = defaultdict(list)
        for entry in entries(monthly.read_text(encoding="utf-8")):
            match = DATE.search(entry)
            if not match: raise ValueError(f"Undated entry in {monthly}")
            grouped[match.group(3)].append(entry)
        for day, items in grouped.items(): write_day(monthly.parent / monthly.stem / f"{day}.md", items)
        monthly.unlink()

def validate() -> bool:
    old = DESTINATION / "legacy" / "task_ledger.pre-migration.md"
    archived = list(DESTINATION.glob("20??/??/??.md"))
    if not old.is_file() or not archived: return False
    old_ids = {item for item in re.findall(r"^### (TASK-[^\s]+)", old.read_text(encoding="utf-8"), re.MULTILINE) if item != "TASK-YYYYMMDD-NNN"}
    new_ids = set()
    for path in archived: new_ids.update(re.findall(r"^### (TASK-[^\s]+)", path.read_text(encoding="utf-8"), re.MULTILINE))
    return old_ids <= new_ids

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("action", choices=("partition", "validate")); args = parser.parse_args()
    if args.action == "partition": partition(); return 0
    print("PASS" if validate() else "FAIL"); return 0 if validate() else 1

if __name__ == "__main__": raise SystemExit(main())
