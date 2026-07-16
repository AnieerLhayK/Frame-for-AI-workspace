#!/usr/bin/env python3
"""Conservative, read-only Git merge preflight.

It proves only path-disjoint changes safe to continue.  Any overlapping path,
rename, deletion, or structured record/config change is a STOP for a human
owner; this module never performs a merge or fabricates semantic intent.
"""
from __future__ import annotations
import argparse, json, subprocess
from pathlib import Path

from scripts.workspace.runtime import WORKSPACE_ROOT as ROOT
STRUCTURED = (".json", ".yaml", ".yml")

def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode: raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()

def changes(base: str, tip: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in git("diff", "--name-status", "--find-renames", base, tip).splitlines():
        parts = line.split("\t"); status = parts[0]
        if status.startswith(("R", "C")) and len(parts) == 3:
            result[parts[1]] = status; result[parts[2]] = status
        elif len(parts) >= 2: result[parts[1]] = status
    return result

def assess(base_ref: str, head_ref: str, target_ref: str) -> dict:
    ancestor = git("merge-base", head_ref, target_ref)
    left, right = changes(ancestor, head_ref), changes(ancestor, target_ref)
    overlaps = sorted(set(left) & set(right))
    findings = []
    for path in overlaps:
        category = "structured_object" if path.endswith(STRUCTURED) else "path_overlap"
        if "/task_records/" in f"/{path}" or "/task_ledger/" in f"/{path}": category = "task_record_overlap"
        if left[path].startswith(("R", "D")) or right[path].startswith(("R", "D")): category = "move_delete_overlap"
        findings.append({"path": path, "category": category, "left_status": left[path], "right_status": right[path], "action": "STOP_HUMAN_ARBITRATION"})
    status = "SAFE_TO_CONTINUE" if not findings else "STOP"
    return {"status": status, "base": ancestor, "head": head_ref, "target": target_ref, "left_changes": sorted(left), "right_changes": sorted(right), "findings": findings, "rollback": "No mutation performed; discard the isolated worktree or branch to abandon the proposed merge.", "validation": ["git diff --check after an actual merge", "workspace workflow check <task-id>", "run affected routed validators"]}

def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only conservative merge preflight.")
    parser.add_argument("target", help="Branch, tag, or commit proposed for merge.")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    try: payload = assess("", args.head, args.target)
    except RuntimeError as error: payload = {"status": "ERROR", "error": str(error)}
    if args.format == "json": print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Merge preflight: {payload['status']}")
        for item in payload.get("findings", []): print(f"STOP {item['category']}: {item['path']}")
    return 0 if payload["status"] == "SAFE_TO_CONTINUE" else 1
if __name__ == "__main__": raise SystemExit(main())
