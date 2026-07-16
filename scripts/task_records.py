#!/usr/bin/env python3
"""Record, validate, and gate durable workspace task outcomes.

The public interface is deliberately small: ``start``, ``init``, ``require``,
``finalize``, ``show``, ``summary``, and ``validate``.  ``require`` is the
single seam used by write gates; callers do not need to know record storage or
registration compatibility details.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RECORD_ROOT = ROOT / "PROJECT_CONTEXT" / "task_records"
SCHEMA_PATH = RECORD_ROOT / "schema.json"
TASK_ID = re.compile(r"^TASK-\d{8}-[A-Za-z0-9-]+$")
STATUSES = {"in_progress", "successful", "failed", "cancelled"}
VALIDATIONS = {"not_run", "passed", "failed", "blocked"}
USABILITY = {"unknown", "usable", "limited", "unusable"}
OPERATIONS = {"workspace_write", "external_write"}


def timestamp(value: str | None = None) -> str:
    if value:
        dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value
    return (
        dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def record_path(task_id: str, started_at: str) -> Path:
    parsed = dt.datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    return (
        RECORD_ROOT
        / f"{parsed:%Y}"
        / f"{parsed:%m}"
        / f"{parsed:%d}"
        / f"{task_id}.json"
    )


def read_record(task_id: str) -> tuple[Path, dict[str, Any]]:
    matches = list(RECORD_ROOT.glob(f"*/*/*/{task_id}.json"))
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one record for {task_id}; found {len(matches)}"
        )
    return matches[0], json.loads(matches[0].read_text(encoding="utf-8"))


def write_record(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def create_record(path: Path, record: dict[str, Any]) -> None:
    """Create once so concurrently started tasks never overwrite each other."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def initial_record(
    task_id: str,
    *,
    task_type: str,
    started_at: str,
    tokens_estimated: int | None,
    operations: list[str],
) -> dict[str, Any]:
    if not TASK_ID.match(task_id):
        raise ValueError("task_id must start with TASK-YYYYMMDD-")
    if not operations:
        raise ValueError("at least one --operation is required")
    unknown = sorted(set(operations) - OPERATIONS)
    if unknown:
        raise ValueError(f"invalid registration operation: {', '.join(unknown)}")
    return {
        "schema_version": "1.1",
        "task_id": task_id,
        "task_type": task_type,
        "started_at": started_at,
        "ended_at": None,
        "status": "in_progress",
        "registration": {"operations": sorted(set(operations))},
        "validation": {"status": "not_run", "commands": [], "evidence": []},
        "human_edit_rounds": 0,
        "tokens": {
            "estimated": tokens_estimated,
            "actual": None,
            "saved": None,
            "currency_cost": None,
        },
        "usability": {"status": "unknown", "evidence": []},
        "notes": [],
    }


def validate_record(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in (
        "schema_version",
        "task_id",
        "started_at",
        "status",
        "validation",
        "human_edit_rounds",
        "tokens",
        "usability",
    ):
        if key not in record:
            errors.append(f"missing {key}")
    if not TASK_ID.match(str(record.get("task_id", ""))):
        errors.append("invalid task_id")
    if record.get("status") not in STATUSES:
        errors.append("invalid status")
    if record.get("validation", {}).get("status") not in VALIDATIONS:
        errors.append("invalid validation.status")
    if record.get("usability", {}).get("status") not in USABILITY:
        errors.append("invalid usability.status")
    if (
        not isinstance(record.get("human_edit_rounds"), int)
        or record.get("human_edit_rounds", -1) < 0
    ):
        errors.append("human_edit_rounds must be non-negative integer")
    tokens = record.get("tokens", {})
    for key in ("estimated", "actual", "saved"):
        if tokens.get(key) is not None and (
            not isinstance(tokens[key], int) or tokens[key] < 0
        ):
            errors.append(f"tokens.{key} must be a non-negative integer or null")
    registration = record.get("registration")
    if registration is not None:
        operations = registration.get("operations") if isinstance(registration, dict) else None
        if not isinstance(operations, list) or not operations:
            errors.append("registration.operations must be a non-empty list")
        elif set(operations) - OPERATIONS:
            errors.append("registration.operations contains an invalid operation")
    if (
        record.get("status") == "successful"
        and record.get("validation", {}).get("status") == "not_run"
    ):
        errors.append("successful records require validation")
    return errors


def active_registration(task_id: str, operation: str) -> dict[str, Any]:
    """Return the active record or raise a caller-ready registration error."""
    if operation not in OPERATIONS:
        raise ValueError(f"invalid registration operation: {operation}")
    path, record = read_record(task_id)
    errors = validate_record(record)
    if errors:
        raise ValueError(f"invalid task record {task_id}: {'; '.join(errors)}")
    if record.get("status") != "in_progress":
        raise ValueError(f"task record {task_id} is not active")
    registration = record.get("registration")
    operations = registration.get("operations", []) if isinstance(registration, dict) else []
    if operation not in operations:
        raise ValueError(
            f"task record {task_id} is not registered for {operation}"
        )
    try:
        display_path = str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        display_path = str(path)
    return {
        "task_id": task_id,
        "operation": operation,
        "path": display_path,
        "status": "active",
        "task_type": record.get("task_type"),
    }


def init(args: argparse.Namespace) -> dict[str, Any]:
    started_at = timestamp(args.started_at)
    path = record_path(args.task_id, started_at)
    record = initial_record(
        args.task_id,
        task_type=args.task_type,
        started_at=started_at,
        tokens_estimated=args.tokens_estimated,
        operations=args.operation,
    )
    try:
        create_record(path, record)
    except FileExistsError as error:
        raise ValueError(f"Record already exists: {path.relative_to(ROOT)}") from error
    return record


def start(args: argparse.Namespace) -> dict[str, Any]:
    started_at = timestamp(args.started_at)
    parsed = dt.datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    folder = RECORD_ROOT / f"{parsed:%Y}" / f"{parsed:%m}" / f"{parsed:%d}"
    existing = {
        path.stem
        for path in folder.glob(f"TASK-{parsed:%Y%m%d}-*.json")
        if path.is_file()
    }
    for sequence in range(1, 10_000):
        task_id = f"TASK-{parsed:%Y%m%d}-{sequence:03d}"
        if task_id in existing:
            continue
        path = folder / f"{task_id}.json"
        record = initial_record(
            task_id,
            task_type=args.task_type,
            started_at=started_at,
            tokens_estimated=args.tokens_estimated,
            operations=args.operation,
        )
        try:
            create_record(path, record)
            return record
        except FileExistsError:
            continue
    raise ValueError("could not allocate a task record id for this day")


def finalize(args: argparse.Namespace) -> dict[str, Any]:
    path, record = read_record(args.task_id)
    record.update(
        {
            "ended_at": timestamp(args.ended_at),
            "status": args.status,
            "human_edit_rounds": args.human_edit_rounds,
        }
    )
    record["validation"]["status"] = args.validation
    record["validation"]["commands"] = args.command
    record["usability"]["status"] = args.usability
    record["tokens"].update(
        {
            "actual": args.tokens_actual,
            "saved": args.tokens_saved,
            "currency_cost": args.currency_cost,
        }
    )
    errors = validate_record(record)
    if errors:
        raise ValueError("; ".join(errors))
    write_record(path, record)
    return record


def records() -> list[dict[str, Any]]:
    result = []
    for path in RECORD_ROOT.glob("*/*/*/TASK-*.json"):
        result.append(json.loads(path.read_text(encoding="utf-8")))
    return sorted(result, key=lambda item: item["started_at"], reverse=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Manage structured workspace task outcome records."
    )
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("start", help="Allocate and register an active task record.")
    p.add_argument("--task-type", required=True)
    p.add_argument("--operation", action="append", choices=sorted(OPERATIONS), required=True)
    p.add_argument("--started-at")
    p.add_argument("--tokens-estimated", type=int)
    p = sub.add_parser("init", help="Register a caller-supplied task record id.")
    p.add_argument("task_id")
    p.add_argument("--task-type", required=True)
    p.add_argument("--operation", action="append", choices=sorted(OPERATIONS), required=True)
    p.add_argument("--started-at")
    p.add_argument("--tokens-estimated", type=int)
    p = sub.add_parser("require", help="Verify an active task registration for a write.")
    p.add_argument("task_id")
    p.add_argument("--operation", choices=sorted(OPERATIONS), required=True)
    p = sub.add_parser("finalize")
    p.add_argument("task_id")
    p.add_argument("--status", choices=sorted(STATUSES), required=True)
    p.add_argument("--validation", choices=sorted(VALIDATIONS), required=True)
    p.add_argument("--usability", choices=sorted(USABILITY), required=True)
    p.add_argument("--human-edit-rounds", type=int, required=True)
    p.add_argument("--command", action="append", default=[])
    p.add_argument("--ended-at")
    p.add_argument("--tokens-actual", type=int)
    p.add_argument("--tokens-saved", type=int)
    p.add_argument("--currency-cost", type=float)
    p = sub.add_parser("show")
    p.add_argument("task_id")
    sub.add_parser("summary")
    sub.add_parser("validate")
    args = parser.parse_args()
    try:
        if args.action == "start":
            output = start(args)
        elif args.action == "init":
            output = init(args)
        elif args.action == "require":
            output = active_registration(args.task_id, args.operation)
        elif args.action == "finalize":
            output = finalize(args)
        elif args.action == "show":
            _, output = read_record(args.task_id)
        elif args.action == "validate":
            failures = {
                item["task_id"]: validate_record(item)
                for item in records()
                if validate_record(item)
            }
            output = {"valid": not failures, "failures": failures, "records": len(records())}
            if failures:
                print(json.dumps(output, ensure_ascii=False, indent=2))
                return 1
        else:
            items = records()
            output = {
                "records": len(items),
                "in_progress": sum(item["status"] == "in_progress" for item in items),
                "successful": sum(item["status"] == "successful" for item in items),
                "validation_passed": sum(
                    item["validation"]["status"] == "passed" for item in items
                ),
                "token_estimated": sum(item["tokens"]["estimated"] or 0 for item in items),
                "token_actual": sum(item["tokens"]["actual"] or 0 for item in items),
                "token_saved": sum(item["tokens"]["saved"] or 0 for item in items),
            }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"task records: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
