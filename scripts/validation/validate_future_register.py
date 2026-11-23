#!/usr/bin/env python3
"""Validate active and historical potential-for-future registries."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from scripts.workspace.runtime import WORKSPACE_ROOT


REGISTRY_ROOT = WORKSPACE_ROOT / "PROJECT_CONTEXT" / "potential_for_future"
SCHEMA_VERSION = "0.2"
REGISTRIES = (
    {
        "name": "optimization_options",
        "path": "optimization_options.yaml",
        "history_path": "history/optimization_options.yaml",
        "source_registry": "PROJECT_CONTEXT/potential_for_future/optimization_options.yaml",
        "entry_key": "options",
        "active_statuses": {"candidate", "active"},
        "history_statuses": {"implemented", "rejected"},
    },
    {
        "name": "risk_register",
        "path": "risk_register.yaml",
        "history_path": "history/risk_register.yaml",
        "source_registry": "PROJECT_CONTEXT/potential_for_future/risk_register.yaml",
        "entry_key": "risks",
        "active_statuses": {"candidate", "observed"},
        "history_statuses": {"mitigated", "accepted", "retired"},
    },
)


@dataclass(frozen=True)
class Finding:
    path: str
    message: str


def _load_mapping(path: Path, findings: list[Finding]) -> dict[str, Any] | None:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except (OSError, yaml.YAMLError) as exc:
        findings.append(Finding(str(path), f"cannot parse YAML: {exc}"))
        return None
    if not isinstance(payload, dict):
        findings.append(Finding(str(path), "document root must be a mapping"))
        return None
    if str(payload.get("schema_version", "")) != SCHEMA_VERSION:
        findings.append(Finding(str(path), f"schema_version must be {SCHEMA_VERSION}"))
    return payload


def _validate_entries(
    payload: dict[str, Any],
    *,
    path: Path,
    entry_key: str,
    allowed_statuses: set[str],
    is_history: bool,
    source_registry: str,
    seen_ids: dict[str, str],
    findings: list[Finding],
) -> None:
    entries = payload.get(entry_key)
    if not isinstance(entries, list):
        findings.append(Finding(str(path), f"{entry_key} must be a list"))
        return
    for index, entry in enumerate(entries, start=1):
        label = f"{entry_key}[{index}]"
        if not isinstance(entry, dict):
            findings.append(Finding(str(path), f"{label} must be a mapping"))
            continue
        title = entry.get("title")
        if not isinstance(title, str) or not title.strip():
            findings.append(Finding(str(path), f"{label} requires a non-empty title"))
        entry_id = entry.get("id")
        if not isinstance(entry_id, str) or not entry_id:
            findings.append(Finding(str(path), f"{label} requires a non-empty id"))
        elif entry_id in seen_ids:
            findings.append(
                Finding(str(path), f"{label} duplicates id {entry_id} from {seen_ids[entry_id]}")
            )
        else:
            seen_ids[entry_id] = str(path)
        status = entry.get("status")
        if status not in allowed_statuses:
            findings.append(
                Finding(str(path), f"{label} has disallowed status {status!r}")
            )
        if not is_history:
            continue
        archived_at = entry.get("archived_at")
        if not isinstance(archived_at, str):
            findings.append(Finding(str(path), f"{label} requires archived_at as YYYY-MM-DD text"))
        else:
            try:
                date.fromisoformat(archived_at)
            except ValueError:
                findings.append(Finding(str(path), f"{label} archived_at is not YYYY-MM-DD"))
        if entry.get("source_registry") != source_registry:
            findings.append(
                Finding(str(path), f"{label} source_registry must be {source_registry}"))


def validate(root: Path = REGISTRY_ROOT) -> list[Finding]:
    """Return all registry-boundary violations without changing any files."""
    findings: list[Finding] = []
    seen_ids: dict[str, str] = {}
    for registry in REGISTRIES:
        active_path = root / str(registry["path"])
        history_path = root / str(registry["history_path"])
        active = _load_mapping(active_path, findings)
        history = _load_mapping(history_path, findings)
        if active is not None:
            _validate_entries(
                active,
                path=active_path,
                entry_key=str(registry["entry_key"]),
                allowed_statuses=set(registry["active_statuses"]),
                is_history=False,
                source_registry=str(registry["path"]),
                seen_ids=seen_ids,
                findings=findings,
            )
        if history is not None:
            _validate_entries(
                history,
                path=history_path,
                entry_key=str(registry["entry_key"]),
                allowed_statuses=set(registry["history_statuses"]),
                is_history=True,
                source_registry=str(registry["source_registry"]),
                seen_ids=seen_ids,
                findings=findings,
            )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate potential-for-future registry boundaries.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    findings = validate()
    payload = {"status": "PASS" if not findings else "FAIL", "findings": [asdict(item) for item in findings]}
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    elif findings:
        print("Potential-for-future registry: FAIL")
        for finding in findings:
            print(f"- {finding.path}: {finding.message}")
    else:
        print("Potential-for-future registry: PASS")
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
