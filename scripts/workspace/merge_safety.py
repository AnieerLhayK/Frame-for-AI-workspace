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
from scripts.workspace.agent_governance import load_registry, load_yaml
from scripts.workspace.task_records import read_record
STRUCTURED = (".json", ".yaml", ".yml")
POLICY_PATH = ROOT / "shared" / "agent_governance.yaml"

def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode: raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def git_returncode(*args: str) -> int:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False).returncode

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


def merge_review_note(record_id: str, source: str, target: str, strategy: str) -> dict | None:
    _, record = read_record(record_id)
    for note in reversed(record.get("notes", [])):
        if not isinstance(note, dict) or note.get("kind") != "merge_review":
            continue
        if (
            note.get("source_branch") == source
            and note.get("target_branch") == target
            and note.get("strategy") == strategy
        ):
            return note
    return None


def governed_assess(source: str, target: str, *, agent: str | None, record_id: str | None, strategy: str) -> dict:
    policy = load_yaml(POLICY_PATH)
    governance = policy.get("git_branch_governance", {})
    allowed_strategies = set(governance.get("allowed_one_shot_strategies", []))
    payload = assess("", source, target)
    findings = list(payload["findings"])
    errors: list[str] = []
    review = {
        "required": True,
        "command": f"code-review {target}",
        "comparison": f"git diff {target}...{source}",
        "status": "REVIEW_REQUIRED",
    }
    if strategy not in allowed_strategies:
        errors.append(f"strategy {strategy} is not permitted")
    if target != governance.get("integration_branch", "main"):
        errors.append(f"managed integration target must be {governance.get('integration_branch', 'main')}")
    if agent:
        expected = load_registry().get("agents", {}).get(agent, {}).get("git_branch")
        if expected and source != expected:
            errors.append(f"{agent} merges must originate from {expected}")
        if not record_id:
            errors.append("--record-id is required for an agent-governed integration")
    if git("status", "--porcelain"):
        errors.append("working tree must be clean before merge preflight")
    if strategy == "ff-only" and git_returncode("merge-base", "--is-ancestor", target, source) != 0:
        errors.append(f"{target} is not an ancestor of {source}; ff-only is impossible")
    for branch in governance.get("managed_branches", []):
        if branch == source:
            continue
        if (
            git_returncode("merge-base", "--is-ancestor", branch, source) != 0
            and git_returncode("merge-base", "--is-ancestor", branch, target) != 0
        ):
            errors.append(f"managed branch {branch} has unmerged commits and cannot be fast-forwarded")
    if record_id:
        note = merge_review_note(record_id, source, target, strategy)
        if note is None:
            errors.append("merge review note is missing")
        else:
            review["status"] = note["status"]
            review["note"] = note
    if errors:
        payload["status"] = "STOP"
    payload.update({"strategy": strategy, "agent": agent, "task_record": record_id, "review": review, "errors": errors})
    return payload

def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only conservative merge preflight.")
    parser.add_argument("target", help="Branch, tag, or commit proposed for merge.")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--agent")
    parser.add_argument("--record-id")
    parser.add_argument("--strategy", choices=("ff-only", "merge-commit"), default="ff-only")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    try: payload = governed_assess(args.head, args.target, agent=args.agent, record_id=args.record_id, strategy=args.strategy)
    except RuntimeError as error: payload = {"status": "ERROR", "error": str(error)}
    if args.format == "json": print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Merge preflight: {payload['status']}")
        for item in payload.get("findings", []): print(f"STOP {item['category']}: {item['path']}")
        for error in payload.get("errors", []): print(f"STOP {error}")
        review = payload.get("review", {})
        print(f"Code review: {review.get('status')} ({review.get('comparison', '')})")
    return 0 if payload["status"] == "SAFE_TO_CONTINUE" else 1
if __name__ == "__main__": raise SystemExit(main())
