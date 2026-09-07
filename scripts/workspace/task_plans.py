#!/usr/bin/env python3
"""Local planning records that coordinate work without granting write authority."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

from scripts.workspace.project_context import TASK_RECORDS_ROOT
from scripts.workspace.runtime import WORKSPACE_ROOT as ROOT

RECORD_ROOT = TASK_RECORDS_ROOT
PLAN_ID = re.compile(r"^PLAN-\d{8}-\d{3}$")
MAP_ID = re.compile(r"^MAP-\d{8}-\d{3}$")
PLAN_KINDS = {"spec", "ticket", "triage", "decision"}
PLAN_STATUSES = {"draft", "ready", "claimed", "in_progress", "completed", "cancelled"}
MAP_STATUSES = {"active", "completed", "archived"}


def timestamp(value: str | None = None) -> str:
    if value:
        dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def record_path(record_id: str, created_at: str) -> Path:
    parsed = dt.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    return RECORD_ROOT / f"{parsed:%Y}" / f"{parsed:%m}" / f"{parsed:%d}" / f"{record_id}.json"


def _read(record_id: str) -> tuple[Path, dict[str, Any]]:
    matches = list(RECORD_ROOT.glob(f"*/*/*/{record_id}.json"))
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one planning record for {record_id}; found {len(matches)}")
    return matches[0], json.loads(matches[0].read_text(encoding="utf-8"))


def read_plan(plan_id: str) -> tuple[Path, dict[str, Any]]:
    if not PLAN_ID.match(plan_id):
        raise ValueError("plan id must use PLAN-YYYYMMDD-NNN")
    return _read(plan_id)


def read_map(map_id: str) -> tuple[Path, dict[str, Any]]:
    if not MAP_ID.match(map_id):
        raise ValueError("map id must use MAP-YYYYMMDD-NNN")
    return _read(map_id)


def write(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def create(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _next_id(prefix: str, created_at: str) -> str:
    parsed = dt.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    folder = RECORD_ROOT / f"{parsed:%Y}" / f"{parsed:%m}" / f"{parsed:%d}"
    existing = {path.stem for path in folder.glob(f"{prefix}-{parsed:%Y%m%d}-*.json")}
    for sequence in range(1, 10_000):
        record_id = f"{prefix}-{parsed:%Y%m%d}-{sequence:03d}"
        if record_id not in existing:
            return record_id
    raise ValueError(f"could not allocate a {prefix} id for this day")


def plans() -> list[dict[str, Any]]:
    result = [json.loads(path.read_text(encoding="utf-8")) for path in RECORD_ROOT.glob("*/*/*/PLAN-*.json")]
    return sorted(result, key=lambda item: (item["created_at"], item["plan_id"]), reverse=True)


def maps() -> list[dict[str, Any]]:
    result = [json.loads(path.read_text(encoding="utf-8")) for path in RECORD_ROOT.glob("*/*/*/MAP-*.json")]
    return sorted(result, key=lambda item: (item["created_at"], item["map_id"]), reverse=True)


def _as_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{field} must be a list of non-empty strings")
    return value


def validate_plan(record: dict[str, Any], *, known_ids: set[str] | None = None) -> list[str]:
    errors: list[str] = []
    required = ("schema_version", "record_kind", "plan_id", "created_at", "updated_at", "title", "kind", "description", "acceptance_criteria", "depends_on", "status", "execution_task_ids", "source_refs")
    for key in required:
        if key not in record:
            errors.append(f"missing {key}")
    if record.get("schema_version") != "1.0" or record.get("record_kind") != "plan":
        errors.append("plan must use record_kind plan and schema_version 1.0")
    if not PLAN_ID.match(str(record.get("plan_id", ""))):
        errors.append("invalid plan_id")
    for key in ("created_at", "updated_at"):
        try:
            timestamp(record.get(key))
        except (TypeError, ValueError):
            errors.append(f"invalid {key}")
    if not isinstance(record.get("title"), str) or not record.get("title").strip():
        errors.append("title must be non-empty")
    if record.get("kind") not in PLAN_KINDS:
        errors.append("invalid plan kind")
    if not isinstance(record.get("description"), str):
        errors.append("description must be a string")
    for key in ("acceptance_criteria", "depends_on", "execution_task_ids", "source_refs"):
        try:
            values = _as_string_list(record.get(key), key)
            if len(values) != len(set(values)):
                errors.append(f"duplicate {key} entry")
        except ValueError as error:
            errors.append(str(error))
    dependencies = record.get("depends_on", [])
    if any(not PLAN_ID.match(value) for value in dependencies if isinstance(value, str)):
        errors.append("depends_on must contain PLAN ids")
    if record.get("plan_id") in dependencies:
        errors.append("a plan cannot depend on itself")
    if known_ids is not None:
        for dependency in dependencies:
            if dependency not in known_ids:
                errors.append(f"missing dependency {dependency}")
    if record.get("status") not in PLAN_STATUSES:
        errors.append("invalid plan status")
    claim = record.get("claim")
    if claim is not None:
        if not isinstance(claim, dict):
            errors.append("claim must be an object or null")
        else:
            for key in ("actor", "claimed_at", "expires_at"):
                if not isinstance(claim.get(key), str) or not claim[key]:
                    errors.append(f"claim requires {key}")
            try:
                if claim.get("expires_at") and dt.datetime.fromisoformat(claim["expires_at"].replace("Z", "+00:00")) <= dt.datetime.fromisoformat(claim["claimed_at"].replace("Z", "+00:00")):
                    errors.append("claim expiry must follow claim time")
            except (TypeError, ValueError):
                errors.append("invalid claim timestamp")
    if record.get("status") in {"claimed", "in_progress"} and claim is None:
        errors.append("claimed and in_progress plans require a claim")
    return errors


def validate_map(record: dict[str, Any], *, known_plan_ids: set[str] | None = None) -> list[str]:
    errors: list[str] = []
    required = ("schema_version", "record_kind", "map_id", "created_at", "updated_at", "title", "destination", "status", "plan_ids", "decisions", "not_yet_specified", "out_of_scope")
    for key in required:
        if key not in record:
            errors.append(f"missing {key}")
    if record.get("schema_version") != "1.0" or record.get("record_kind") != "map":
        errors.append("map must use record_kind map and schema_version 1.0")
    if not MAP_ID.match(str(record.get("map_id", ""))):
        errors.append("invalid map_id")
    if not isinstance(record.get("title"), str) or not record.get("title").strip():
        errors.append("map title must be non-empty")
    if not isinstance(record.get("destination"), str) or not record.get("destination").strip():
        errors.append("map destination must be non-empty")
    if record.get("status") not in MAP_STATUSES:
        errors.append("invalid map status")
    for key in ("plan_ids", "not_yet_specified", "out_of_scope"):
        try:
            values = _as_string_list(record.get(key), key)
            if len(values) != len(set(values)):
                errors.append(f"duplicate {key} entry")
        except ValueError as error:
            errors.append(str(error))
    if any(not PLAN_ID.match(value) for value in record.get("plan_ids", []) if isinstance(value, str)):
        errors.append("map plan_ids must contain PLAN ids")
    if known_plan_ids is not None:
        for plan_id in record.get("plan_ids", []):
            if plan_id not in known_plan_ids:
                errors.append(f"map references missing plan {plan_id}")
    decisions = record.get("decisions")
    if not isinstance(decisions, list):
        errors.append("decisions must be a list")
    else:
        for item in decisions:
            if not isinstance(item, dict) or not PLAN_ID.match(str(item.get("plan_id", ""))) or not isinstance(item.get("summary"), str) or not item["summary"].strip():
                errors.append("decisions entries require a plan_id and summary")
    return errors


def _cycle_errors(records: list[dict[str, Any]]) -> list[str]:
    by_id = {item["plan_id"]: item for item in records}
    visiting: set[str] = set()
    visited: set[str] = set()
    errors: list[str] = []

    def visit(plan_id: str) -> None:
        if plan_id in visited:
            return
        if plan_id in visiting:
            errors.append(f"dependency cycle includes {plan_id}")
            return
        visiting.add(plan_id)
        for dependency in by_id[plan_id].get("depends_on", []):
            if dependency in by_id:
                visit(dependency)
        visiting.remove(plan_id)
        visited.add(plan_id)

    for plan_id in by_id:
        visit(plan_id)
    return errors


def validate_all() -> dict[str, Any]:
    plan_records = plans()
    plan_ids = {item.get("plan_id", "") for item in plan_records}
    failures: dict[str, list[str]] = {}
    for item in plan_records:
        errors = validate_plan(item, known_ids=plan_ids)
        if errors:
            failures[item.get("plan_id", "(unknown)")] = errors
    cycles = _cycle_errors(plan_records)
    if cycles:
        failures["dependencies"] = cycles
    for item in maps():
        errors = validate_map(item, known_plan_ids=plan_ids)
        if errors:
            failures[item.get("map_id", "(unknown)")] = errors
    return {"valid": not failures, "failures": failures, "plans": len(plan_records), "maps": len(maps())}


def _dependencies_complete(record: dict[str, Any]) -> bool:
    for dependency in record["depends_on"]:
        _, parent = read_plan(dependency)
        if parent.get("status") != "completed":
            return False
    return True


def _expired(claim: dict[str, Any], now: str) -> bool:
    return dt.datetime.fromisoformat(claim["expires_at"].replace("Z", "+00:00")) <= dt.datetime.fromisoformat(now.replace("Z", "+00:00"))


def create_plan(args: argparse.Namespace) -> dict[str, Any]:
    created_at = timestamp(args.created_at)
    plan_id = _next_id("PLAN", created_at)
    record = {
        "schema_version": "1.0", "record_kind": "plan", "plan_id": plan_id,
        "created_at": created_at, "updated_at": created_at, "title": args.title,
        "kind": args.kind, "description": args.description,
        "acceptance_criteria": args.acceptance_criterion, "depends_on": args.depends_on,
        "status": "draft", "claim": None, "execution_task_ids": [], "source_refs": args.source_ref,
    }
    errors = validate_plan(record, known_ids={item["plan_id"] for item in plans()})
    if errors:
        raise ValueError("; ".join(errors))
    create(record_path(plan_id, created_at), record)
    return record


def create_map(args: argparse.Namespace) -> dict[str, Any]:
    created_at = timestamp(args.created_at)
    map_id = _next_id("MAP", created_at)
    record = {
        "schema_version": "1.0", "record_kind": "map", "map_id": map_id,
        "created_at": created_at, "updated_at": created_at, "title": args.title,
        "destination": args.destination, "status": "active", "plan_ids": [], "decisions": [],
        "not_yet_specified": args.not_yet_specified, "out_of_scope": args.out_of_scope,
    }
    errors = validate_map(record, known_plan_ids={item["plan_id"] for item in plans()})
    if errors:
        raise ValueError("; ".join(errors))
    create(record_path(map_id, created_at), record)
    return record


def set_plan_status(args: argparse.Namespace) -> dict[str, Any]:
    path, record = read_plan(args.plan_id)
    if args.status == "ready" and not _dependencies_complete(record):
        raise ValueError("cannot mark a plan ready until every dependency is completed")
    if args.status == "completed" and record.get("status") != "in_progress":
        raise ValueError("only an in_progress plan can be completed")
    if args.status in {"claimed", "in_progress"}:
        raise ValueError("use claim or linked task start for claimed/in_progress state")
    record["status"] = args.status
    if args.status in {"draft", "ready", "cancelled"}:
        record["claim"] = None
    record["updated_at"] = timestamp(args.updated_at)
    errors = validate_plan(record, known_ids={item["plan_id"] for item in plans()})
    if errors:
        raise ValueError("; ".join(errors))
    write(path, record)
    return record


def claim_plan(args: argparse.Namespace) -> dict[str, Any]:
    path, record = read_plan(args.plan_id)
    now = timestamp(args.now)
    claim = record.get("claim")
    if claim is not None and not _expired(claim, now) and claim.get("actor") != args.actor:
        raise ValueError(f"plan is claimed by {claim['actor']} until {claim['expires_at']}")
    if record.get("status") not in {"ready", "claimed"}:
        raise ValueError("only a ready plan can be claimed")
    if args.hours <= 0:
        raise ValueError("claim duration must be positive")
    if not _dependencies_complete(record):
        raise ValueError("cannot claim a plan with incomplete dependencies")
    expires_at = (dt.datetime.fromisoformat(now.replace("Z", "+00:00")) + dt.timedelta(hours=args.hours)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    record["claim"] = {"actor": args.actor, "claimed_at": now, "expires_at": expires_at}
    record["status"] = "claimed"
    record["updated_at"] = now
    write(path, record)
    return record


def renew_claim(args: argparse.Namespace) -> dict[str, Any]:
    path, record = read_plan(args.plan_id)
    now = timestamp(args.now)
    claim = record.get("claim")
    if not isinstance(claim, dict) or claim.get("actor") != args.actor:
        raise ValueError("only the current claimant can renew a claim")
    if _expired(claim, now):
        raise ValueError("expired claims must be claimed again")
    if args.hours <= 0:
        raise ValueError("claim duration must be positive")
    expires_at = (dt.datetime.fromisoformat(now.replace("Z", "+00:00")) + dt.timedelta(hours=args.hours)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    claim["expires_at"] = expires_at
    record["updated_at"] = now
    write(path, record)
    return record


def release_claim(args: argparse.Namespace) -> dict[str, Any]:
    path, record = read_plan(args.plan_id)
    claim = record.get("claim")
    if not isinstance(claim, dict) or claim.get("actor") != args.actor:
        raise ValueError("only the current claimant can release a claim")
    record["claim"] = None
    record["status"] = "ready" if _dependencies_complete(record) else "draft"
    record["updated_at"] = timestamp(args.updated_at)
    write(path, record)
    return record


def execution_ready(plan_id: str) -> None:
    _, record = read_plan(plan_id)
    if record.get("status") != "claimed" or not isinstance(record.get("claim"), dict):
        raise ValueError("a plan must have an active claim before execution starts")
    if _expired(record["claim"], timestamp()):
        raise ValueError("the plan claim expired before execution started")
    if not _dependencies_complete(record):
        raise ValueError("cannot start a plan with incomplete dependencies")


def link_execution(plan_id: str, task_id: str) -> dict[str, Any]:
    path, record = read_plan(plan_id)
    execution_ready(plan_id)
    if task_id not in record["execution_task_ids"]:
        record["execution_task_ids"].append(task_id)
    record["status"] = "in_progress"
    record["updated_at"] = timestamp()
    write(path, record)
    return record


def record_execution_outcome(plan_id: str, task_id: str, task_status: str) -> dict[str, Any]:
    path, record = read_plan(plan_id)
    if task_id not in record["execution_task_ids"]:
        raise ValueError(f"task {task_id} is not linked to {plan_id}")
    if task_status == "successful":
        record["status"] = "completed"
        record["claim"] = None
    elif task_status in {"failed", "cancelled"}:
        record["status"] = "claimed"
    record["updated_at"] = timestamp()
    write(path, record)
    return record


def add_map_plan(args: argparse.Namespace) -> dict[str, Any]:
    path, record = read_map(args.map_id)
    read_plan(args.plan_id)
    if args.plan_id not in record["plan_ids"]:
        record["plan_ids"].append(args.plan_id)
    record["updated_at"] = timestamp(args.updated_at)
    write(path, record)
    return record


def add_map_decision(args: argparse.Namespace) -> dict[str, Any]:
    path, record = read_map(args.map_id)
    _, plan = read_plan(args.plan_id)
    if plan.get("status") != "completed":
        raise ValueError("only a completed plan can be recorded as a map decision")
    record["decisions"].append({"plan_id": args.plan_id, "summary": args.summary})
    record["updated_at"] = timestamp(args.updated_at)
    write(path, record)
    return record


def require_write_authorization(record_id: str) -> None:
    """PLAN/MAP mutations share the normal TASK write gate; plans grant nothing."""
    from scripts.workspace import task_records

    task_records.active_registration(record_id, "workspace_write")


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage local Workspace planning records.")
    sub = parser.add_subparsers(dest="action", required=True)
    plan_create = sub.add_parser("create")
    plan_create.add_argument("--title", required=True)
    plan_create.add_argument("--kind", choices=sorted(PLAN_KINDS), required=True)
    plan_create.add_argument("--description", required=True)
    plan_create.add_argument("--acceptance-criterion", action="append", default=[])
    plan_create.add_argument("--depends-on", action="append", default=[])
    plan_create.add_argument("--source-ref", action="append", default=[])
    plan_create.add_argument("--created-at"); plan_create.add_argument("--record-id", required=True)
    plan_show = sub.add_parser("show"); plan_show.add_argument("plan_id")
    sub.add_parser("list")
    plan_status = sub.add_parser("set-status"); plan_status.add_argument("plan_id"); plan_status.add_argument("--status", choices=sorted(PLAN_STATUSES - {"claimed", "in_progress"}), required=True); plan_status.add_argument("--updated-at"); plan_status.add_argument("--record-id", required=True)
    for action in ("claim", "renew", "release"):
        command = sub.add_parser(action); command.add_argument("plan_id"); command.add_argument("--actor", required=True)
        if action in {"claim", "renew"}:
            command.add_argument("--hours", type=int, default=24)
            command.add_argument("--now")
        else:
            command.add_argument("--updated-at")
        command.add_argument("--record-id", required=True)
    map_create = sub.add_parser("map-create"); map_create.add_argument("--title", required=True); map_create.add_argument("--destination", required=True); map_create.add_argument("--not-yet-specified", action="append", default=[]); map_create.add_argument("--out-of-scope", action="append", default=[]); map_create.add_argument("--created-at"); map_create.add_argument("--record-id", required=True)
    map_show = sub.add_parser("map-show"); map_show.add_argument("map_id")
    sub.add_parser("map-list")
    map_plan = sub.add_parser("map-add-plan"); map_plan.add_argument("map_id"); map_plan.add_argument("plan_id"); map_plan.add_argument("--updated-at"); map_plan.add_argument("--record-id", required=True)
    map_decision = sub.add_parser("map-add-decision"); map_decision.add_argument("map_id"); map_decision.add_argument("plan_id"); map_decision.add_argument("--summary", required=True); map_decision.add_argument("--updated-at"); map_decision.add_argument("--record-id", required=True)
    sub.add_parser("validate")
    args = parser.parse_args()
    try:
        if args.action in {"create", "set-status", "claim", "renew", "release", "map-create", "map-add-plan", "map-add-decision"}:
            require_write_authorization(args.record_id)
        if args.action == "create": output = create_plan(args)
        elif args.action == "show": _, output = read_plan(args.plan_id)
        elif args.action == "list": output = plans()
        elif args.action == "set-status": output = set_plan_status(args)
        elif args.action == "claim": output = claim_plan(args)
        elif args.action == "renew": output = renew_claim(args)
        elif args.action == "release": output = release_claim(args)
        elif args.action == "map-create": output = create_map(args)
        elif args.action == "map-show": _, output = read_map(args.map_id)
        elif args.action == "map-list": output = maps()
        elif args.action == "map-add-plan": output = add_map_plan(args)
        elif args.action == "map-add-decision": output = add_map_decision(args)
        else:
            output = validate_all()
            if not output["valid"]:
                print(json.dumps(output, ensure_ascii=False, indent=2)); return 1
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"task plans: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
