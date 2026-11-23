"""Neutral TASK persistence and registration validation; no authorization decisions.

Governance owns actor identity, capabilities and path authority. This module
only reads records and validates their storage/liveness contract.
"""
from __future__ import annotations
import datetime as dt
import json
import re
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
            approval = note.get("governance_approval")
            if approval is not None:
                if not isinstance(approval, dict):
                    errors.append("governance_approval must be an object")
                elif (approval.get("approver") not in {"codex", "user"}
                      or not str(approval.get("evidence", "")).strip()
                      or approval.get("scope") != "integrate_and_publish"
                      or any(not approval.get(key) or approval.get(key) != note.get(key)
                             for key in ("source_commit", "target_commit"))
                      or (approval.get("approver") == "codex" and not approval.get("record_id"))):
                    errors.append("invalid governance delivery approval")
    registration = record.get("registration")
    if registration is not None:
        operations = registration.get("operations") if isinstance(registration, dict) else None
        if not isinstance(operations, list) or not operations:
            errors.append("registration.operations must be a non-empty list")
        elif set(operations) - OPERATIONS:
            errors.append("registration.operations contains an invalid operation")
    schema_version = str(record.get("schema_version", ""))
    baseline = record.get("git_baseline")
    if schema_version == "1.4" and baseline is None:
        errors.append("schema 1.4 records require git_baseline")
    if baseline is not None:
        if not isinstance(baseline, dict):
            errors.append("git_baseline must be an object")
        else:
            for key in ("branch", "head_commit", "captured_at"):
                if not isinstance(baseline.get(key), str) or not baseline[key]:
                    errors.append(f"git_baseline.{key} must be a non-empty string")
            paths = baseline.get("paths")
            if not isinstance(paths, list):
                errors.append("git_baseline.paths must be a list")
            else:
                seen_paths: set[str] = set()
                for entry in paths:
                    if not isinstance(entry, dict):
                        errors.append("git_baseline.paths entries must be objects")
                        continue
                    path = entry.get("path")
                    if not isinstance(path, str) or not path:
                        errors.append("git_baseline path must be a non-empty string")
                        continue
                    normalized = path.replace("\\", "/").casefold()
                    if normalized in seen_paths:
                        errors.append(f"duplicate git_baseline path: {path}")
                    seen_paths.add(normalized)
                    for key in ("index_status", "worktree_status"):
                        value = entry.get(key)
                        if not isinstance(value, str) or len(value) != 1:
                            errors.append(
                                f"git_baseline path {path} has invalid {key}"
                            )
                    for key in ("index_blob", "worktree_sha256"):
                        value = entry.get(key)
                        if value is not None and not isinstance(value, str):
                            errors.append(
                                f"git_baseline path {path} has invalid {key}"
                            )
    origin = record.get("origin")
    if origin is not None:
        if not isinstance(origin, dict) or origin.get("kind") != "external_workspace":
            errors.append("origin must describe an external workspace")
        elif not isinstance(origin.get("agent"), str) or not origin["agent"]:
            errors.append("external origin requires an agent")
        elif not isinstance(origin.get("client_root"), str) or not origin["client_root"]:
            errors.append("external origin requires a client_root")
    owner = record.get("owner")
    if owner is not None:
        if not isinstance(owner, dict) or owner.get("kind") != "workspace_session":
            errors.append("owner must describe a workspace session")
        else:
            if not isinstance(owner.get("agent"), str) or not owner["agent"]:
                errors.append("workspace session owner requires an agent")
            if not isinstance(owner.get("session_id"), str) or not owner["session_id"]:
                errors.append("workspace session owner requires a session_id")
            bindings = owner.get("bindings")
            if not isinstance(bindings, list) or any(
                not isinstance(binding, str) or not binding for binding in bindings
            ):
                errors.append("workspace session owner requires string bindings")
    plan_id = record.get("plan_id")
    if plan_id is not None and (not isinstance(plan_id, str) or not re.match(r"^PLAN-\d{8}-\d{3}$", plan_id)):
        errors.append("plan_id must use PLAN-YYYYMMDD-NNN")
    if (
        record.get("status") == "successful"
        and record.get("validation", {}).get("status") == "not_run"
    ):
        errors.append("successful records require validation")
    return errors

def active_registration(
    task_id: str, operation: str, *, allow_external_origin: bool = False,
    expected_task_type: str | None = None, expected_bindings: list[str] | None = None,
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
    if expected_task_type and record.get("task_type") != expected_task_type:
        raise ValueError(
            f"task record {task_id} task type {record.get('task_type')!r}; expected {expected_task_type!r}"
        )
    owner = record.get("owner")
    recorded_bindings = owner.get("bindings", []) if isinstance(owner, dict) else []
    missing_bindings = sorted(set(expected_bindings or []) - set(recorded_bindings))
    if missing_bindings:
        raise ValueError(f"task record {task_id} missing exact binding(s): " + ", ".join(missing_bindings))
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
        "origin": origin,
        "git_baseline": record.get("git_baseline"),
        "schema_version": record.get("schema_version"),
    }

def records() -> list[dict[str, Any]]:
    result = []
    for path in RECORD_ROOT.glob("*/*/*/TASK-*.json"):
        result.append(json.loads(path.read_text(encoding="utf-8")))
    return sorted(result, key=lambda item: item["started_at"], reverse=True)


def active_external_registration(
    task_id: str, *, agent: str, client_root: str
) -> dict[str, Any]:
    """Verify an external caller is using its own active origin record."""
    registration = active_registration(
        task_id, "workspace_write", allow_external_origin=True
    )
    _, record = read_record(task_id)
    origin = record.get("origin")
    expected_agent = agent
    expected_root = external_client_root(client_root)
    if not isinstance(origin, dict) or origin.get("kind") != "external_workspace":
        raise ValueError("task record is not registered for an external workspace")
    if origin.get("agent") != expected_agent:
        raise ValueError("external task agent does not match the task origin")
    if origin.get("client_root") != expected_root:
        raise ValueError("external client root does not match the task origin")
    return registration
