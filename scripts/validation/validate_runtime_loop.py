#!/usr/bin/env python3
"""Read-only audit of runtime-loop packets, links, ledgers, and state evidence."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path.cwd()
LOOP = Path("packages/character-system/reports/runtime-loop")
FENCE = re.compile(r"```yaml\s*\n(.*?)\n```", re.DOTALL)
ID_PATTERN = re.compile(r"^(DIAG|HANDOFF|CASE|PATCH|VAL|GEN)-\d{8}-\d{3}$")
KINDS = {
    "diagnoses": ("diagnosis", ("diagnosis_id",), "DIAG"),
    "handoffs": ("handoff", ("handoff_id", "case_handoff_id"), ("HANDOFF", "CASE")),
    "patches": ("patch", ("patch_id",), "PATCH"),
    "validations": ("validation", ("validation_id",), "VAL"),
    "generalization_backlog": ("generalization", ("generalization_id",), "GEN"),
}


@dataclass
class Finding:
    severity: str
    message: str


@dataclass
class Packet:
    packet_id: str
    kind: str
    path: Path
    data: dict[str, Any]


def add(findings: list[Finding], severity: str, message: str) -> None:
    findings.append(Finding(severity, message))


def first_value(data: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        if data.get(key):
            return str(data[key])
    return ""


def parse_packets(root: Path, findings: list[Finding]) -> dict[str, Packet]:
    packets: dict[str, Packet] = {}
    loop = root / LOOP
    for directory, (kind, id_keys, prefixes) in KINDS.items():
        allowed = (prefixes,) if isinstance(prefixes, str) else prefixes
        for path in sorted((loop / directory).glob("*.md")):
            if path.name.startswith("README"):
                continue
            match = FENCE.search(path.read_text(encoding="utf-8-sig", errors="replace"))
            if not match:
                add(findings, "ERROR", f"{path.as_posix()}: missing fenced YAML metadata")
                continue
            try:
                data = yaml.safe_load(match.group(1))
            except yaml.YAMLError as exc:
                add(findings, "ERROR", f"{path.as_posix()}: malformed YAML metadata: {str(exc).splitlines()[0]}")
                continue
            if not isinstance(data, dict):
                add(findings, "ERROR", f"{path.as_posix()}: YAML metadata must be a mapping")
                continue
            packet_id = first_value(data, id_keys)
            if not packet_id or not ID_PATTERN.match(packet_id) or not packet_id.startswith(allowed):
                add(findings, "ERROR", f"{path.as_posix()}: missing or invalid {kind} id")
                continue
            if not path.name.startswith(packet_id):
                add(findings, "ERROR", f"{path.as_posix()}: filename does not start with metadata id {packet_id}")
            if packet_id in packets:
                add(findings, "ERROR", f"duplicate packet id {packet_id}: {packets[packet_id].path} and {path}")
                continue
            packets[packet_id] = Packet(packet_id, kind, path, data)
    return packets


def parse_ledger(path: Path, id_column: str, findings: list[Finding]) -> dict[str, dict[str, str]]:
    if not path.is_file():
        add(findings, "ERROR", f"ledger missing: {path.as_posix()}")
        return {}
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    header: list[str] | None = None
    rows: dict[str, dict[str, str]] = {}
    for line in lines:
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if header is None and id_column in cells:
            header = cells
            continue
        if header is None or len(cells) != len(header) or all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        row = dict(zip(header, cells))
        record_id = row.get(id_column, "")
        if not record_id:
            continue
        if record_id in rows:
            add(findings, "ERROR", f"duplicate ledger id {record_id} in {path.as_posix()}")
        rows[record_id] = row
    return rows


def linked(data: dict[str, Any], kind: str) -> str:
    aliases = {
        "diagnosis": ("linked_diagnosis", "linked_diagnosis_id", "diagnosis_id"),
        "handoff": ("linked_handoff", "linked_handoff_id", "handoff_id"),
        "patch": ("linked_patch", "linked_patch_id", "patch_id"),
    }
    return first_value(data, aliases[kind])


def decision_value(value: Any) -> str:
    if isinstance(value, str):
        return value.lower()
    if isinstance(value, dict):
        for choice in ("accepted", "rejected", "deferred"):
            if value.get(choice) is True:
                return choice
    return ""


def validation_state(data: dict[str, Any]) -> str:
    if data.get("validation_status"):
        return str(data["validation_status"]).lower()
    result = str(data.get("pass_or_fail", "")).lower()
    if result == "pass":
        return "validated"
    if result.startswith("objective_pass"):
        return "applied"
    return ""


def check_links_and_states(packets: dict[str, Packet], ledgers: dict[str, dict[str, dict[str, str]]], findings: list[Finding]) -> None:
    for packet in packets.values():
        data = packet.data
        required_link = {"handoff": "diagnosis", "patch": "diagnosis", "validation": "patch", "generalization": "patch"}.get(packet.kind)
        if required_link:
            target_id = linked(data, required_link)
            if not target_id:
                add(findings, "ERROR", f"{packet.packet_id} lacks required linked_{required_link}")
            elif target_id not in packets:
                add(findings, "ERROR", f"{packet.packet_id} references missing {target_id}")
        if packet.kind == "handoff" and packet.packet_id.startswith("CASE-"):
            handoff_id = linked(data, "handoff")
            if handoff_id and handoff_id not in packets:
                add(findings, "ERROR", f"{packet.packet_id} references missing {handoff_id}")
        if packet.kind == "validation":
            patch = packets.get(linked(data, "patch"))
            diag = linked(data, "diagnosis")
            if patch and diag and linked(patch.data, "diagnosis") != diag:
                add(findings, "ERROR", f"{packet.packet_id} diagnosis link conflicts with its patch")

    diagnosis_rows, patch_rows, generalization_rows = ledgers["diagnosis"], ledgers["patch"], ledgers["generalization"]
    for name, prefix, rows in (("diagnosis", "DIAG-", diagnosis_rows), ("patch", "PATCH-", patch_rows), ("generalization", "GEN-", generalization_rows)):
        packet_ids = {key for key in packets if key.startswith(prefix)}
        for record_id in rows:
            if record_id not in packet_ids:
                add(findings, "ERROR", f"{name} ledger references missing packet {record_id}")
        for packet_id in sorted(packet_ids - rows.keys()):
            add(findings, "WARNING", f"historical {name} packet is not in its ledger: {packet_id}")

    diagnosis_states = {"new", "handed_off", "accepted", "patched", "validated", "closed", "rejected", "deferred"}
    patch_decisions = {"accepted", "rejected", "deferred"}
    patch_states = {"proposed", "accepted", "applied", "validated", "closed", "reverted", "deferred"}
    generalization_states = {"candidate", "accepted", "implemented", "validated", "closed", "rejected", "deferred"}
    for record_id, row in diagnosis_rows.items():
        status = row.get("status", "").lower()
        if status not in diagnosis_states:
            add(findings, "ERROR", f"diagnosis ledger {record_id} has invalid status {status!r}")
        handoff = row.get("linked_handoff", "")
        if status in {"handed_off", "accepted", "patched", "validated", "closed"} and handoff not in packets:
            add(findings, "ERROR", f"diagnosis ledger {record_id} status {status} lacks valid handoff evidence")
    for record_id, row in patch_rows.items():
        decision, state = row.get("decision", "").lower(), row.get("validation_status", "").lower()
        if decision not in patch_decisions:
            add(findings, "ERROR", f"patch ledger {record_id} has invalid decision {decision!r}")
        if state not in patch_states:
            add(findings, "ERROR", f"patch ledger {record_id} has invalid validation_status {state!r}")
        packet = packets.get(record_id)
        if packet:
            packet_decision = decision_value(packet.data.get("decision")) or decision_value(packet.data.get("maintainer_decision"))
            if packet_decision and packet_decision != decision:
                add(findings, "ERROR", f"{record_id} packet decision {packet_decision} conflicts with ledger {decision}")
            packet_state = str(packet.data.get("patch_status", "")).lower()
            if packet_state and packet_state != state:
                add(findings, "ERROR", f"{record_id} packet state {packet_state} conflicts with ledger {state}")
        validations = [item for item in packets.values() if item.kind == "validation" and linked(item.data, "patch") == record_id]
        derived = {validation_state(item.data) for item in validations} - {""}
        if derived and state not in derived:
            add(findings, "ERROR", f"{record_id} ledger state {state} conflicts with validation packet state {sorted(derived)}")
        if state == "validated" and "validated" not in derived:
            add(findings, "ERROR", f"patch ledger {record_id} is validated without validation evidence")
    for record_id, row in generalization_rows.items():
        decision, status = row.get("decision", "").lower(), row.get("status", "").lower()
        if decision not in patch_decisions or status not in generalization_states:
            add(findings, "ERROR", f"generalization ledger {record_id} has invalid decision/status")
        packet = packets.get(record_id)
        if packet:
            packet_decision = decision_value(packet.data.get("decision"))
            if packet_decision and packet_decision != decision:
                add(findings, "ERROR", f"{record_id} packet decision {packet_decision} conflicts with ledger {decision}")
            packet_status = str(packet.data.get("status", "")).lower()
            if packet_status and packet_status != status:
                add(findings, "ERROR", f"{record_id} packet status {packet_status} conflicts with ledger {status}")


def audit(root: Path = ROOT) -> tuple[list[Finding], int]:
    findings: list[Finding] = []
    packets = parse_packets(root, findings)
    ledger_root = root / LOOP / "ledgers"
    ledgers = {
        "diagnosis": parse_ledger(ledger_root / "diagnosis_ledger.md", "diagnosis_id", findings),
        "patch": parse_ledger(ledger_root / "patch_ledger.md", "patch_id", findings),
        "generalization": parse_ledger(ledger_root / "generalization_ledger.md", "generalization_id", findings),
    }
    check_links_and_states(packets, ledgers, findings)
    return findings, len(packets)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="Exit 2 when warnings exist without errors.")
    args = parser.parse_args(argv)
    findings, parsed = audit()
    for finding in findings:
        print(f"{finding.severity}: {finding.message}")
    errors = sum(item.severity == "ERROR" for item in findings)
    warnings = sum(item.severity == "WARNING" for item in findings)
    print(f"Parsed packets: {parsed}")
    print(f"ERROR: {errors}")
    print(f"WARNING: {warnings}")
    if errors:
        return 1
    if args.strict and warnings:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
