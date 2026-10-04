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
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from scripts.workspace.project_context import TASK_RECORDS_ROOT
from scripts.workspace.runtime import WORKSPACE_ROOT as ROOT
from scripts.workspace import task_record_store as record_store
from scripts.workspace.task_record_store import (
    SCHEMA_PATH, TASK_ID, STATUSES, VALIDATIONS, USABILITY, OPERATIONS,
    MERGE_REVIEW_STATUSES, USAGE_STATUSES, record_path, read_record, write_record,
    create_record, validate_record, active_registration, external_client_root, records,
)

def __getattr__(name: str):
    if name == "RECORD_ROOT":
        return record_store.RECORD_ROOT
    raise AttributeError(name)


def git_text(arguments: list[str]) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="surrogateescape",
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(
            result.stderr.strip() or f"git {' '.join(arguments)} failed"
        )
    return result.stdout


def worktree_sha256(path: str) -> str | None:
    """Hash one current worktree entry without retaining its contents."""
    relative = PurePosixPath(path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Git reported a path outside the workspace: {path}")
    candidate = ROOT.joinpath(*relative.parts)
    if candidate.is_symlink():
        payload = os.readlink(candidate).encode("utf-8", errors="surrogatepass")
        return hashlib.sha256(payload).hexdigest()
    if not candidate.is_file():
        return None
    digest = hashlib.sha256()
    with candidate.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def capture_git_baseline(*, captured_at: str | None = None) -> dict[str, Any]:
    """Capture bounded Git state for later task-attribution checks."""
    branch = git_text(["branch", "--show-current"]).strip() or "(detached)"
    head_commit = git_text(["rev-parse", "HEAD"]).strip()
    status = git_text(
        ["status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames"]
    )
    paths: list[dict[str, Any]] = []
    for token in status.split("\0"):
        if not token:
            continue
        if len(token) < 4 or token[2] != " ":
            raise ValueError("Git returned malformed porcelain status")
        index_status, worktree_status = token[0], token[1]
        path = token[3:].replace("\\", "/")
        index_line = git_text(["ls-files", "--stage", "--", path]).splitlines()
        index_blob = None
        if index_line:
            fields = index_line[0].split(maxsplit=2)
            if len(fields) >= 2:
                index_blob = fields[1]
        paths.append(
            {
                "path": path,
                "index_status": index_status,
                "worktree_status": worktree_status,
                "index_blob": index_blob,
                "worktree_sha256": worktree_sha256(path),
            }
        )
    return {
        "branch": branch,
        "head_commit": head_commit,
        "captured_at": timestamp(captured_at),
        "paths": sorted(paths, key=lambda item: item["path"].casefold()),
    }


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


def initial_record(
    task_id: str,
    *,
    task_type: str,
    started_at: str,
    tokens_estimated: int | None,
    operations: list[str],
    owner: dict[str, Any] | None = None,
    git_baseline: dict[str, Any] | None = None,
    plan_id: str | None = None,
) -> dict[str, Any]:
    if not TASK_ID.match(task_id):
        raise ValueError("task_id must start with TASK-YYYYMMDD-")
    if not operations:
        raise ValueError("at least one --operation is required")
    unknown = sorted(set(operations) - OPERATIONS)
    if unknown:
        raise ValueError(f"invalid registration operation: {', '.join(unknown)}")
    record = {
        "schema_version": "1.4" if git_baseline is not None else "1.3",
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
    if plan_id is not None:
        record["plan_id"] = plan_id
    if owner is not None:
        record["owner"] = owner
    if git_baseline is not None:
        record["git_baseline"] = git_baseline
    return record


def workspace_session_owner(args: argparse.Namespace) -> dict[str, Any] | None:
    """Return optional durable ownership stamped by an in-workspace adapter."""
    agent = str(getattr(args, "owner_agent", None) or "").strip()
    session_id = str(getattr(args, "owner_session", None) or "").strip()
    if not agent and not session_id:
        return None
    if not agent or not session_id:
        raise ValueError("--owner-agent and --owner-session must be supplied together")
    return {
        "kind": "workspace_session",
        "agent": agent,
        "session_id": session_id,
        "bindings": sorted(set(getattr(args, "bind", []))),
    }


def resolve_tokens_estimated(task_type: str, bindings: list[str]) -> int:
    """Measure the initial routed context when a caller did not supply it."""
    from scripts.workspace.resolve_task_context import parse_bindings, resolve_task

    resolved = resolve_task(
        workspace_root=ROOT,
        task_id=task_type,
        bindings=parse_bindings(bindings),
        include_optional=False,
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
    from scripts.workspace.agent_governance import external_agent_id as resolve_actor
    return resolve_actor(name)


def init(args: argparse.Namespace) -> dict[str, Any]:
    started_at = timestamp(args.started_at)
    git_baseline = capture_git_baseline(captured_at=started_at)
    path = record_path(args.task_id, started_at)
    record = initial_record(
        args.task_id,
        task_type=args.task_type,
        started_at=started_at,
        tokens_estimated=tokens_estimated(args),
        operations=args.operation,
        git_baseline=git_baseline,
        plan_id=getattr(args, "plan_id", None),
    )
    try:
        create_record(path, record)
    except FileExistsError as error:
        raise ValueError(f"Record already exists: {path.relative_to(ROOT)}") from error
    return record


def start(args: argparse.Namespace) -> dict[str, Any]:
    started_at = timestamp(args.started_at)
    git_baseline = capture_git_baseline(captured_at=started_at)
    parsed = dt.datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    folder = record_store.RECORD_ROOT / f"{parsed:%Y}" / f"{parsed:%m}" / f"{parsed:%d}"
    existing = {
        path.stem
        for path in folder.glob(f"TASK-{parsed:%Y%m%d}-*.json")
        if path.is_file()
    }
    estimate = tokens_estimated(args)
    plan_id = getattr(args, "plan_id", None)
    if plan_id:
        from scripts.workspace import task_plans
        task_plans.execution_ready(plan_id)
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
            owner=workspace_session_owner(args),
            git_baseline=git_baseline,
            plan_id=plan_id,
        )
        try:
            create_record(path, record)
            if plan_id:
                from scripts.workspace import task_plans
                task_plans.link_execution(plan_id, task_id)
            return record
        except FileExistsError:
            continue
    raise ValueError("could not allocate a task record id for this day")


def external_start(args: argparse.Namespace) -> dict[str, Any]:
    if "workspace_write" not in args.operation:
        raise ValueError("external workspace tasks must declare workspace_write")
    if "external_write" in args.operation:
        raise ValueError(
            "external-start records provenance only; register external_write "
            "separately after target authorization"
        )
    agent = external_agent_id(args.agent)
    client_root = external_client_root(args.client_root)
    record = start(args)
    path = record_path(record["task_id"], record["started_at"])
    record["origin"] = {
        "kind": "external_workspace",
        "agent": agent,
        "client_root": client_root,
        "bindings": sorted(set(getattr(args, "bind", []))),
    }
    errors = validate_record(record)
    if errors:
        raise ValueError("; ".join(errors))
    write_record(path, record)
    return record


def active_external_registration(task_id: str, *, agent: str, client_root: str) -> dict[str, Any]:
    """Compatibility entry: resolve actor authority before neutral origin checks."""
    return record_store.active_external_registration(
        task_id, agent=external_agent_id(agent), client_root=client_root
    )


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
    record.setdefault("schema_version", "1.3")
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
    if args.currency_cost is not None:
        record["tokens"]["currency_cost"] = args.currency_cost
    elif usage["status"] == "recorded" and usage["currency_cost"] is not None:
        record["tokens"]["currency_cost"] = usage["currency_cost"]
    record["usage"] = usage
    errors = validate_record(record)
    if errors:
        raise ValueError("; ".join(errors))
    write_record(path, record)
    if record.get("plan_id"):
        from scripts.workspace import task_plans
        task_plans.record_execution_outcome(record["plan_id"], record["task_id"], args.status)
    from scripts.workspace.task_ledger import upsert_task_record

    upsert_task_record(path, record)
    return record


def ensure_audit_not_delivered(task_id: str, target: str) -> None:
    path, _ = read_record(task_id)
    relative = path.relative_to(ROOT).as_posix()
    delivered = json.loads(git_text(["show", f"{target}:{relative}"]))
    if any(isinstance(note, dict) and note.get("kind") == "merge_review"
           and note.get("audit_close") and note.get("status") == "completed"
           for note in delivered.get("notes", [])):
        raise ValueError("audit closure already delivered for this TASK")


def add_merge_review_note(args: argparse.Namespace) -> dict[str, Any]:
    path, record = read_record(args.task_id)
    audit_close = getattr(args, "audit_close", False)
    if audit_close:
        if record.get("status") != "successful" or record.get("validation", {}).get("status") != "passed":
            raise ValueError("audit closure requires a successfully finalized, validated task")
        ensure_audit_not_delivered(args.task_id, args.target_branch)
    elif record.get("status") != "in_progress":
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
    if args.status == "completed":
        commands = getattr(args, "validation_command", [])
        if not commands:
            raise ValueError("completed review requires --validation-command evidence")
        note.update({
            "source_commit": git_text(["rev-parse", args.source_branch]).strip(),
            "target_commit": git_text(["rev-parse", args.target_branch]).strip(),
            "validation": {"status": "passed", "commands": commands},
            "ready_tasks": sorted(set(getattr(args, "ready_task", []))),
            "audit_close": audit_close,
        })
    approver = getattr(args, "governance_approver", None)
    if approver:
        if args.status != "completed" or not getattr(args, "approval_evidence", None):
            raise ValueError("governance approval requires completed review and --approval-evidence")
        approving_task = getattr(args, "approver_record_id", None)
        if approver == "codex":
            from scripts.workspace.agent_governance import require_task_actor
            if not approving_task:
                raise ValueError("Codex approval requires --approver-record-id")
            require_task_actor(approving_task, "codex", "workspace_write")
        note["governance_approval"] = {
            "approver": approver, "record_id": approving_task,
            "evidence": args.approval_evidence,
            "scope": "integrate_and_publish",
            "source_commit": note["source_commit"], "target_commit": note["target_commit"],
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
        command.add_argument("--plan-id")

    p = sub.add_parser("start", help="Allocate and register an active task record.")
    add_registration_arguments(p)
    p.add_argument("--owner-agent")
    p.add_argument("--owner-session")
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
    p.add_argument("--task-type")
    p.add_argument("--bind", action="append", default=[], metavar="NAME=VALUE")
    p.add_argument("--external-client-root")
    p.add_argument("--agent")
    p = sub.add_parser("finalize")
    p.add_argument("task_id")
    p.add_argument("--status", choices=sorted(STATUSES), required=True)
    p.add_argument("--validation", choices=sorted(VALIDATIONS), required=True)
    p.add_argument("--usability", choices=sorted(USABILITY), required=True)
    p.add_argument("--human-edit-rounds", type=int, required=True)
    p.add_argument("--command", action="append", default=[])
    p.add_argument("--ended-at")
    p.add_argument("--tokens-actual", type=int)
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
    p.add_argument("--validation-command", action="append", default=[])
    p.add_argument("--ready-task", action="append", default=[], help="Other active TASK whose owner confirmed this complete batch is ready.")
    p.add_argument("--audit-close", action="store_true", help="Review only final audit files of a successfully finalized TASK.")
    p.add_argument("--governance-approver", choices=("codex", "user"))
    p.add_argument("--approval-evidence", help="Reference to the explicit approval of this exact batch.")
    p.add_argument("--approver-record-id", help="Active Codex-owned TASK for Codex approval.")
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
            if args.external_client_root:
                if not args.agent:
                    raise ValueError("--external-client-root requires --agent")
                active_external_registration(args.task_id, agent=args.agent, client_root=args.external_client_root)
            output = active_registration(args.task_id, args.operation, expected_task_type=args.task_type, expected_bindings=args.bind, allow_external_origin=bool(args.external_client_root))
            if args.agent and not args.external_client_root:
                from scripts.workspace.agent_governance import require_task_actor
                require_task_actor(args.task_id, args.agent, args.operation)
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
