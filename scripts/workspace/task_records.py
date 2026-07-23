#!/usr/bin/env python3
"""Record, validate, and gate durable workspace task outcomes.

The public interface is deliberately small: ``start``, ``external-start``,
``report-usage``, ``init``, ``require``, ``finalize``, ``show``, ``summary``,
and ``validate``.  ``require`` is the single seam used by write gates; callers
do not need to know record storage or registration compatibility details.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from scripts.workspace.project_context import TASK_RECORDS_ROOT
from scripts.workspace.runtime import WORKSPACE_ROOT as ROOT
RECORD_ROOT = TASK_RECORDS_ROOT
SCHEMA_PATH = RECORD_ROOT / "schema.json"
TASK_ID = re.compile(r"^TASK-\d{8}-[A-Za-z0-9-]+$")
STATUSES = {"in_progress", "successful", "failed", "cancelled"}
VALIDATIONS = {"not_run", "passed", "failed", "blocked"}
USABILITY = {"unknown", "usable", "limited", "unusable"}
OPERATIONS = {"workspace_write", "external_write"}
MERGE_REVIEW_STATUSES = {"completed", "skipped_user_approved"}
USAGE_STATUSES = {"recorded", "unavailable", "manual"}


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
        "schema_version": "1.3",
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
        "usage": {
            "status": "unavailable",
            "source": None,
            "transport": None,
            "observed_at": None,
            "reason": "no_host_usage_source",
        },
        "usability": {"status": "unknown", "evidence": []},
        "notes": [],
    }


def resolve_tokens_estimated(task_type: str, bindings: list[str]) -> int:
    """Measure the initial routed context when a caller did not supply it."""
    from scripts.workspace.resolve_task_context import parse_bindings, resolve_task

    resolved = resolve_task(
        workspace_root=ROOT,
        task_id=task_type,
        bindings=parse_bindings(bindings),
        include_optional=False,
        include_template=False,
        count_tokens=True,
    )
    errors = resolved.get("errors", [])
    if errors:
        raise ValueError(
            f"could not measure tokens for {task_type}: {'; '.join(errors)}; "
            "pass --tokens-estimated after resolving the task context"
        )
    estimate = resolved.get("token_budget", {}).get("initial_tokens")
    if not isinstance(estimate, int) or estimate < 0:
        raise ValueError(f"resolver returned an invalid token estimate for {task_type}")
    return estimate


def tokens_estimated(args: argparse.Namespace) -> int:
    if args.tokens_estimated is not None:
        return args.tokens_estimated
    return resolve_tokens_estimated(args.task_type, args.bind)


def usage_unavailable(reason: str, *, transport: str | None = None) -> dict[str, Any]:
    return {
        "status": "unavailable",
        "source": None,
        "transport": transport,
        "observed_at": None,
        "reason": reason,
    }


def optional_nonnegative_int(payload: dict[str, Any], key: str) -> int | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"usage field {key} must be a non-negative integer")
    return value


def optional_nonnegative_number(payload: dict[str, Any], key: str) -> float | int | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError(f"usage field {key} must be a non-negative number")
    return value


def host_usage(task_id: str) -> dict[str, Any]:
    """Read one explicit host payload; this never contacts a usage provider."""
    raw = os.environ.get("WORKSPACE_TASK_USAGE_JSON")
    file_path = os.environ.get("WORKSPACE_TASK_USAGE_FILE")
    transport: str | None = None
    if raw:
        transport = "environment"
    elif file_path:
        transport = "file"
        try:
            raw = Path(file_path).read_text(encoding="utf-8")
        except OSError:
            return usage_unavailable("usage_file_unreadable", transport=transport)
    else:
        return usage_unavailable("no_host_usage_source")
    return usage_from_json(raw, task_id=task_id, transport=transport)


def usage_from_json(raw: str, *, task_id: str, transport: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return usage_unavailable("usage_payload_invalid_json", transport=transport)
    return usage_from_payload(payload, task_id=task_id, transport=transport)


def usage_from_payload(
    payload: object, *, task_id: str, transport: str
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return usage_unavailable("usage_payload_not_object", transport=transport)
    if payload.get("task_id") not in (None, task_id):
        return usage_unavailable("usage_task_id_mismatch", transport=transport)
    try:
        total = optional_nonnegative_int(payload, "total_tokens")
        input_tokens = optional_nonnegative_int(payload, "input_tokens")
        output_tokens = optional_nonnegative_int(payload, "output_tokens")
        if total is None and input_tokens is not None and output_tokens is not None:
            total = input_tokens + output_tokens
        if total is None:
            return usage_unavailable("usage_total_missing", transport=transport)
        cost = optional_nonnegative_number(payload, "currency_cost")
    except ValueError as error:
        return usage_unavailable(str(error), transport=transport)
    source = payload.get("source")
    if not isinstance(source, str) or not source.strip():
        return usage_unavailable("usage_source_missing", transport=transport)
    observed_at = payload.get("observed_at")
    return {
        "status": "recorded",
        "source": source.strip(),
        "transport": transport,
        "observed_at": observed_at if isinstance(observed_at, str) else None,
        "reason": None,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total,
        "currency_cost": cost,
    }


def external_agent_id(name: str) -> str:
    """Resolve an active registered actor for an external workspace caller."""
    from scripts.workspace.agent_governance import (
        effective_registration,
        load_yaml,
        load_manifest,
        load_registry,
        POLICY_PATH,
    )

    resolved = effective_registration(
        load_yaml(POLICY_PATH), load_registry(), load_manifest(), name
    )
    if (
        not resolved["registered"]
        or resolved["registration_status"] != "active"
        or resolved["degraded"]
    ):
        raise ValueError("external task callers must be active registered agents")
    return str(resolved["agent"])


def external_client_root(value: str) -> str:
    client_root = Path(value).expanduser()
    if not client_root.is_absolute():
        raise ValueError("--client-root must be an absolute path")
    client_root = client_root.resolve()
    workspace_root = ROOT.resolve()
    if client_root == workspace_root or workspace_root in client_root.parents:
        raise ValueError("--client-root must be outside the workspace root")
    if not client_root.is_dir():
        raise ValueError("--client-root must be an existing directory")
    return str(client_root)


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
    if tokens.get("currency_cost") is not None and (
        isinstance(tokens["currency_cost"], bool)
        or not isinstance(tokens["currency_cost"], (int, float))
        or tokens["currency_cost"] < 0
    ):
        errors.append("tokens.currency_cost must be a non-negative number or null")
    usage = record.get("usage")
    if usage is not None:
        if not isinstance(usage, dict) or usage.get("status") not in USAGE_STATUSES:
            errors.append("usage must be an object with a valid status")
        elif usage["status"] in {"recorded", "manual"}:
            if not isinstance(usage.get("source"), str) or not usage["source"]:
                errors.append("recorded usage requires a source")
            if usage["status"] == "recorded" and tokens.get("actual") is None:
                errors.append("recorded usage requires tokens.actual")
    notes = record.get("notes", [])
    if not isinstance(notes, list):
        errors.append("notes must be a list")
    for note in notes if isinstance(notes, list) else []:
        if isinstance(note, str):
            continue
        if not isinstance(note, dict):
            errors.append("notes entries must be strings or objects")
            continue
        if note.get("kind") == "merge_review":
            if note.get("status") not in MERGE_REVIEW_STATUSES:
                errors.append("merge_review note has invalid status")
            for key in ("source_branch", "target_branch", "strategy", "review_base"):
                if not isinstance(note.get(key), str) or not note[key]:
                    errors.append(f"merge_review note missing {key}")
            if note.get("status") == "skipped_user_approved" and not note.get("reason"):
                errors.append("skipped merge_review note requires reason")
    registration = record.get("registration")
    if registration is not None:
        operations = registration.get("operations") if isinstance(registration, dict) else None
        if not isinstance(operations, list) or not operations:
            errors.append("registration.operations must be a non-empty list")
        elif set(operations) - OPERATIONS:
            errors.append("registration.operations contains an invalid operation")
    origin = record.get("origin")
    if origin is not None:
        if not isinstance(origin, dict) or origin.get("kind") != "external_workspace":
            errors.append("origin must describe an external workspace")
        elif not isinstance(origin.get("agent"), str) or not origin["agent"]:
            errors.append("external origin requires an agent")
        elif not isinstance(origin.get("client_root"), str) or not origin["client_root"]:
            errors.append("external origin requires a client_root")
    if (
        record.get("status") == "successful"
        and record.get("validation", {}).get("status") == "not_run"
    ):
        errors.append("successful records require validation")
    return errors


def active_registration(
    task_id: str, operation: str, *, allow_external_origin: bool = False
) -> dict[str, Any]:
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
    origin = record.get("origin")
    if (
        isinstance(origin, dict)
        and origin.get("kind") == "external_workspace"
        and not allow_external_origin
    ):
        raise ValueError("external task records require --external-client-root")
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
        tokens_estimated=tokens_estimated(args),
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
    estimate = tokens_estimated(args)
    for sequence in range(1, 10_000):
        task_id = f"TASK-{parsed:%Y%m%d}-{sequence:03d}"
        if task_id in existing:
            continue
        path = folder / f"{task_id}.json"
        record = initial_record(
            task_id,
            task_type=args.task_type,
            started_at=started_at,
            tokens_estimated=estimate,
            operations=args.operation,
        )
        try:
            create_record(path, record)
            return record
        except FileExistsError:
            continue
    raise ValueError("could not allocate a task record id for this day")


def external_start(args: argparse.Namespace) -> dict[str, Any]:
    if "workspace_write" not in args.operation:
        raise ValueError("external workspace tasks must declare workspace_write")
    agent = external_agent_id(args.agent)
    client_root = external_client_root(args.client_root)
    record = start(args)
    path = record_path(record["task_id"], record["started_at"])
    record["origin"] = {
        "kind": "external_workspace",
        "agent": agent,
        "client_root": client_root,
    }
    errors = validate_record(record)
    if errors:
        raise ValueError("; ".join(errors))
    write_record(path, record)
    return record


def active_external_registration(
    task_id: str, *, agent: str, client_root: str
) -> dict[str, Any]:
    """Verify an external caller is using its own active origin record."""
    registration = active_registration(
        task_id, "workspace_write", allow_external_origin=True
    )
    _, record = read_record(task_id)
    origin = record.get("origin")
    expected_agent = external_agent_id(agent)
    expected_root = external_client_root(client_root)
    if not isinstance(origin, dict) or origin.get("kind") != "external_workspace":
        raise ValueError("task record is not registered for an external workspace")
    if origin.get("agent") != expected_agent:
        raise ValueError("external task agent does not match the task origin")
    if origin.get("client_root") != expected_root:
        raise ValueError("external client root does not match the task origin")
    return registration


def report_usage(args: argparse.Namespace) -> dict[str, Any]:
    path, record = read_record(args.task_id)
    if record.get("status") != "in_progress":
        raise ValueError("usage reports require an active task record")
    origin = record.get("origin")
    if not isinstance(origin, dict) or origin.get("kind") != "external_workspace":
        raise ValueError("usage reports require an external workspace task record")
    if external_agent_id(args.agent) != origin.get("agent"):
        raise ValueError("usage-reporting agent does not match the task origin")
    if args.usage_json is not None:
        usage = usage_from_json(
            args.usage_json, task_id=record["task_id"], transport="external_cli"
        )
    else:
        usage_path = Path(args.usage_file).resolve()
        client_root = Path(str(origin["client_root"])).resolve()
        try:
            usage_path.relative_to(client_root)
        except ValueError as error:
            raise ValueError("usage file must be inside the external client root") from error
        if not usage_path.is_file():
            raise ValueError("usage file is unreadable")
        try:
            raw = usage_path.read_text(encoding="utf-8")
        except OSError as error:
            raise ValueError("usage file is unreadable") from error
        usage = usage_from_json(raw, task_id=record["task_id"], transport="external_file")
    if usage["status"] != "recorded":
        raise ValueError(f"usage report rejected: {usage['reason']}")
    record["tokens"]["actual"] = usage["total_tokens"]
    if usage["currency_cost"] is not None:
        record["tokens"]["currency_cost"] = usage["currency_cost"]
    record["usage"] = usage
    errors = validate_record(record)
    if errors:
        raise ValueError("; ".join(errors))
    write_record(path, record)
    return record


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
    record["schema_version"] = "1.3"
    usage = host_usage(record["task_id"])
    existing_usage = record.get("usage")
    if (
        usage["status"] == "unavailable"
        and isinstance(existing_usage, dict)
        and existing_usage.get("status") == "recorded"
    ):
        usage = existing_usage
    if args.tokens_actual is not None:
        record["tokens"]["actual"] = args.tokens_actual
        usage = {
            "status": "manual",
            "source": "finalize_cli",
            "transport": "command_argument",
            "observed_at": None,
            "reason": None,
        }
    elif usage["status"] == "recorded":
        record["tokens"]["actual"] = usage["total_tokens"]
    if args.tokens_saved is not None:
        record["tokens"]["saved"] = args.tokens_saved
    if args.currency_cost is not None:
        record["tokens"]["currency_cost"] = args.currency_cost
    elif usage["status"] == "recorded" and usage["currency_cost"] is not None:
        record["tokens"]["currency_cost"] = usage["currency_cost"]
    record["usage"] = usage
    errors = validate_record(record)
    if errors:
        raise ValueError("; ".join(errors))
    write_record(path, record)
    from scripts.workspace.task_ledger import upsert_task_record

    upsert_task_record(path, record)
    return record


def add_merge_review_note(args: argparse.Namespace) -> dict[str, Any]:
    path, record = read_record(args.task_id)
    if record.get("status") != "in_progress":
        raise ValueError("merge review notes require an active task record")
    if args.status == "skipped_user_approved" and not args.reason:
        raise ValueError("--reason is required when review is skipped")
    note = {
        "kind": "merge_review",
        "status": args.status,
        "source_branch": args.source_branch,
        "target_branch": args.target_branch,
        "strategy": args.strategy,
        "review_base": args.review_base,
        "reason": args.reason,
    }
    record.setdefault("notes", []).append(note)
    errors = validate_record(record)
    if errors:
        raise ValueError("; ".join(errors))
    write_record(path, record)
    return record


def sync_ledger(args: argparse.Namespace) -> dict[str, Any]:
    """Backfill finalized records into the human-readable task ledger."""
    from scripts.workspace.task_ledger import sync_records

    synced = sync_records(task_id=args.task_id, day=args.date)
    return {"synced": synced, "count": len(synced)}


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
    def add_registration_arguments(command: argparse.ArgumentParser) -> None:
        command.add_argument("--task-type", required=True)
        command.add_argument("--operation", action="append", choices=sorted(OPERATIONS), required=True)
        command.add_argument("--started-at")
        command.add_argument("--tokens-estimated", type=int)
        command.add_argument("--bind", action="append", default=[], metavar="NAME=VALUE")

    p = sub.add_parser("start", help="Allocate and register an active task record.")
    add_registration_arguments(p)
    p = sub.add_parser("external-start", help="Register a workspace task initiated from an external workspace.")
    p.add_argument("--agent", required=True)
    p.add_argument("--client-root", required=True)
    add_registration_arguments(p)
    p = sub.add_parser("init", help="Register a caller-supplied task record id.")
    p.add_argument("task_id")
    p.add_argument("--task-type", required=True)
    p.add_argument("--operation", action="append", choices=sorted(OPERATIONS), required=True)
    p.add_argument("--started-at")
    p.add_argument("--tokens-estimated", type=int)
    p.add_argument("--bind", action="append", default=[], metavar="NAME=VALUE")
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
    p = sub.add_parser("report-usage", help="Write verified external-host usage into an active external task.")
    p.add_argument("task_id")
    p.add_argument("--agent", required=True)
    usage_input = p.add_mutually_exclusive_group(required=True)
    usage_input.add_argument("--usage-json")
    usage_input.add_argument("--usage-file")
    p = sub.add_parser("note-merge-review", help="Record merge review or a user-approved skip.")
    p.add_argument("task_id")
    p.add_argument("--status", choices=sorted(MERGE_REVIEW_STATUSES), required=True)
    p.add_argument("--source-branch", required=True)
    p.add_argument("--target-branch", default="main")
    p.add_argument("--strategy", choices=("ff-only", "merge-commit"), default="ff-only")
    p.add_argument("--review-base", default="main")
    p.add_argument("--reason")
    p = sub.add_parser("show")
    p.add_argument("task_id")
    p = sub.add_parser("sync-ledger", help="Backfill finalized records into the task ledger.")
    p.add_argument("--task-id")
    p.add_argument("--date", help="ISO date (YYYY-MM-DD) for backfill")
    sub.add_parser("summary")
    sub.add_parser("validate")
    args = parser.parse_args()
    try:
        if args.action == "start":
            output = start(args)
        elif args.action == "external-start":
            output = external_start(args)
        elif args.action == "init":
            output = init(args)
        elif args.action == "require":
            output = active_registration(args.task_id, args.operation)
        elif args.action == "finalize":
            output = finalize(args)
        elif args.action == "report-usage":
            output = report_usage(args)
        elif args.action == "note-merge-review":
            output = add_merge_review_note(args)
        elif args.action == "show":
            _, output = read_record(args.task_id)
        elif args.action == "sync-ledger":
            output = sync_ledger(args)
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
                "usage_recorded": sum(item.get("usage", {}).get("status") == "recorded" for item in items),
                "usage_unavailable": sum(item.get("usage", {}).get("status") == "unavailable" for item in items),
            }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"task records: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
