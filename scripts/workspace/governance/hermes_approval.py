"""Validate and approve the fixed Hermes workspace-guard hooks.

The public seam remains ``scripts.workspace.agent_governance``.  This module
owns the external allowlist mechanics so agent registration and Hermes hook
approval can evolve independently.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml


HERMES_GUARD_EVENTS = ("pre_tool_call", "post_tool_call", "pre_llm_call")


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a mapping in {path}")
    return payload


def _utc_mtime(path: Path) -> str:
    return (
        datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _command_references_guard(command: str, guard_script: Path) -> bool:
    return str(guard_script).replace("\\", "/").casefold() in command.replace("\\", "/").casefold()


def inspect_hermes_guard_approval(
    *,
    config_path: Path,
    allowlist_path: Path,
    guard_script: Path,
    guard_events: tuple[str, ...] = HERMES_GUARD_EVENTS,
) -> dict[str, Any]:
    """Validate the fixed workspace-guard hooks before allowlisting them."""
    findings: list[str] = []
    if not guard_script.is_file():
        findings.append(f"workspace guard script is missing: {guard_script}")
    if not config_path.is_file():
        findings.append(f"Hermes config is missing: {config_path}")
    if not allowlist_path.is_file():
        findings.append(f"Hermes allowlist is missing: {allowlist_path}")
    if findings:
        return {"status": "DENY", "operation": "hermes_guard_approval", "reason": "; ".join(findings)}

    config = _load_yaml(config_path)
    hooks = config.get("hooks", {})
    if not isinstance(hooks, dict):
        return {"status": "DENY", "operation": "hermes_guard_approval", "reason": "Hermes hooks configuration is invalid"}
    allowlist = json.loads(allowlist_path.read_text(encoding="utf-8-sig"))
    approvals = allowlist.get("approvals") if isinstance(allowlist, dict) else None
    if not isinstance(approvals, list) or not all(isinstance(item, dict) for item in approvals):
        return {"status": "DENY", "operation": "hermes_guard_approval", "reason": "Hermes allowlist approvals are invalid"}

    entries: list[dict[str, str]] = []
    for event in guard_events:
        configured_hooks = hooks.get(event, [])
        if not isinstance(configured_hooks, list):
            findings.append(f"{event} Hermes hook configuration is invalid")
            continue
        candidates = [
            item for item in configured_hooks
            if isinstance(item, dict) and _command_references_guard(str(item.get("command", "")), guard_script)
        ]
        if len(candidates) != 1:
            findings.append(f"{event} must configure exactly one workspace guard hook")
            continue
        command = str(candidates[0].get("command", "")).strip()
        if not command:
            findings.append(f"{event} workspace guard command is empty")
            continue
        entries.append({"event": event, "command": command})
    if findings:
        return {"status": "DENY", "operation": "hermes_guard_approval", "reason": "; ".join(findings)}

    expected_mtime = _utc_mtime(guard_script)
    updates = [
        {
            **entry,
            "script_path": str(guard_script),
            "script_mtime_at_approval": expected_mtime,
        }
        for entry in entries
    ]
    existing = {(str(item.get("event", "")), str(item.get("command", ""))) for item in approvals}
    return {
        "status": "PASS",
        "operation": "hermes_guard_approval",
        "dry_run": True,
        "allowlist_path": str(allowlist_path),
        "updates": updates,
        "already_current": all(
            (entry["event"], entry["command"]) in existing
            and next(
                item for item in approvals
                if (str(item.get("event", "")), str(item.get("command", ""))) == (entry["event"], entry["command"])
            ).get("script_mtime_at_approval") == expected_mtime
            for entry in entries
        ),
    }


def approve_hermes_guard(
    *,
    record_id: str | None,
    approve: bool,
    config_path: Path,
    allowlist_path: Path,
    guard_script: Path,
    registration_lookup: Callable[[str, str], dict[str, Any]],
    guard_events: tuple[str, ...] = HERMES_GUARD_EVENTS,
) -> dict[str, Any]:
    """Preview or perform the explicit external allowlist update."""
    payload = inspect_hermes_guard_approval(
        config_path=config_path,
        allowlist_path=allowlist_path,
        guard_script=guard_script,
        guard_events=guard_events,
    )
    if payload["status"] != "PASS" or not approve:
        return payload
    if not record_id:
        return {
            "status": "DENY",
            "operation": "hermes_guard_approval",
            "reason": "--record-id is required with --approve",
        }
    try:
        registration = registration_lookup(record_id, "external_write")
    except ValueError as error:
        return {
            "status": "DENY",
            "operation": "hermes_guard_approval",
            "reason": f"task registration denied: {error}",
        }

    allowlist = json.loads(allowlist_path.read_text(encoding="utf-8-sig"))
    updates = payload["updates"]
    update_keys = {(entry["event"], entry["command"]) for entry in updates}
    retained = [
        item for item in allowlist["approvals"]
        if (str(item.get("event", "")), str(item.get("command", ""))) not in update_keys
    ]
    approved_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    retained.extend(
        {
            "event": entry["event"],
            "command": entry["command"],
            "approved_at": approved_at,
            "script_mtime_at_approval": entry["script_mtime_at_approval"],
        }
        for entry in updates
    )
    allowlist["approvals"] = retained
    allowlist_path.write_text(json.dumps(allowlist, indent=2) + "\n", encoding="utf-8")
    return {
        **payload,
        "status": "APPROVED",
        "dry_run": False,
        "task_registration": registration,
    }
