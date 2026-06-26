from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Sequence

import yaml

try:
    from scripts.agent_governance import (
        check_access,
        load_manifest,
        load_registry,
    )
    from scripts.plan_change_surface import (
        WORKSPACE_ROOT,
        is_concrete_scope,
        normalize_path,
        resolve_task,
    )
except ModuleNotFoundError:  # Direct execution: python scripts/verify_change_scope.py
    from agent_governance import check_access, load_manifest, load_registry
    from plan_change_surface import (
        WORKSPACE_ROOT,
        is_concrete_scope,
        normalize_path,
        resolve_task,
    )


GitRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]
TaskResolver = Callable[[str, list[str]], dict[str, Any]]
POLICY_PATH = WORKSPACE_ROOT / "shared" / "agent_governance.yaml"


@dataclass
class Change:
    path: str
    statuses: set[str] = field(default_factory=set)
    sources: set[str] = field(default_factory=set)


def run_git(arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=WORKSPACE_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def require_git(
    runner: GitRunner,
    arguments: Sequence[str],
) -> str:
    result = runner(arguments)
    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or f"git {' '.join(arguments)} failed"
        )
    return result.stdout


def normalize_git_path(value: str) -> str:
    return normalize_path(value).casefold()


def scope_matches(path: str, scope: str) -> bool:
    candidate = normalize_git_path(path)
    allowed = normalize_git_path(scope)
    if allowed == "**":
        return True
    if any(character in allowed for character in "*?["):
        return fnmatch.fnmatchcase(candidate, allowed)
    return candidate == allowed or candidate.startswith(f"{allowed}/")


def parse_name_status(output: str) -> list[tuple[str, str]]:
    parsed: list[tuple[str, str]] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith(("R", "C")) and len(parts) >= 3:
            parsed.append((parts[1], status))
            parsed.append((parts[2], status))
        elif len(parts) >= 2:
            parsed.append((parts[1], status))
    return parsed


def collect_changes(
    *,
    include_staged: bool,
    include_untracked: bool,
    runner: GitRunner = run_git,
) -> tuple[str, list[Change]]:
    branch = require_git(runner, ["branch", "--show-current"]).strip() or "(detached)"
    changes: dict[str, Change] = {}

    def add(path: str, status: str, source: str) -> None:
        normalized = normalize_path(path)
        key = normalize_git_path(normalized)
        record = changes.setdefault(key, Change(path=normalized))
        record.statuses.add(status)
        record.sources.add(source)

    unstaged_names = require_git(runner, ["diff", "--name-only"])
    unstaged_status = require_git(
        runner, ["diff", "--name-status", "--find-renames"]
    )
    status_by_path = {
        normalize_git_path(path): status
        for path, status in parse_name_status(unstaged_status)
    }
    for path in unstaged_names.splitlines():
        if path.strip():
            add(
                path,
                status_by_path.get(normalize_git_path(path), "M"),
                "unstaged",
            )
    for path, status in parse_name_status(unstaged_status):
        add(path, status, "unstaged")

    if include_staged:
        staged_names = require_git(runner, ["diff", "--cached", "--name-only"])
        staged_status = require_git(
            runner, ["diff", "--cached", "--name-status", "--find-renames"]
        )
        status_by_path = {
            normalize_git_path(path): status
            for path, status in parse_name_status(staged_status)
        }
        for path in staged_names.splitlines():
            if path.strip():
                add(
                    path,
                    status_by_path.get(normalize_git_path(path), "M"),
                    "staged",
                )
        for path, status in parse_name_status(staged_status):
            add(path, status, "staged")

    if include_untracked:
        untracked = require_git(
            runner, ["ls-files", "--others", "--exclude-standard"]
        )
        for path in untracked.splitlines():
            if path.strip():
                add(path, "??", "untracked")

    return branch, sorted(changes.values(), key=lambda item: item.path.casefold())


def load_governance_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("agent governance policy must be a mapping")
    return payload


def classify_surface(path: str, policy: dict[str, Any]) -> str:
    for surface in policy.get("surface_classes", []):
        for pattern in surface.get("path_patterns", []):
            if scope_matches(path, str(pattern)):
                return str(surface.get("id", "workspace_other"))
    return "workspace_other"


def risk_assessment(
    change: Change,
    policy: dict[str, Any],
    *,
    rename_count: int,
) -> dict[str, Any]:
    path = normalize_git_path(change.path)
    risk_policy = policy.get("change_risk_policy", {})
    surface = classify_surface(change.path, policy)
    level = "normal"
    reasons: list[str] = []
    operations: list[str] = []

    if surface in set(risk_policy.get("high_surfaces", [])):
        level = "high"
        reasons.append(f"high-risk surface: {surface}")
    if any(
        scope_matches(change.path, str(pattern))
        for pattern in risk_policy.get("high_path_patterns", [])
    ):
        level = "high"
        reasons.append("high-risk governance or boundary path")
    elif any(
        scope_matches(change.path, str(pattern))
        for pattern in risk_policy.get("elevated_path_patterns", [])
    ):
        level = "elevated"
        reasons.append("elevated always-on boundary path")

    renamed = any(status.startswith("R") for status in change.statuses)
    deleted = any(status.startswith("D") for status in change.statuses)
    if renamed:
        level = "high" if rename_count >= 5 else max_risk(level, "elevated")
        reasons.append("file or directory move/rename")
        if rename_count >= 5:
            operations.append("large_move_or_rename")
    if (renamed or deleted) and path.startswith(("skills/", "packages/")):
        level = "high"
        reasons.append("Skill or package deletion/move")
        operations.append("skill_delete_or_move")
    if surface == "platform_projection":
        operations.append("platform_projection_change")
    confirmation_ops = set(
        risk_policy.get("confirmation_required_operations", [])
    )
    worktree_ops = set(risk_policy.get("worktree_recommended_operations", []))
    return {
        "risk_level": level,
        "risk_reasons": list(dict.fromkeys(reasons)),
        "affected_surfaces": [surface],
        "operations": list(dict.fromkeys(operations)),
        "confirmation_required": bool(set(operations) & confirmation_ops),
        "worktree_recommended": bool(set(operations) & worktree_ops),
    }


def max_risk(left: str, right: str) -> str:
    order = {"normal": 0, "elevated": 1, "high": 2}
    return left if order[left] >= order[right] else right


def verify_changes(
    task_id: str,
    bindings: list[str],
    *,
    include_staged: bool = True,
    include_untracked: bool = True,
    agent_id: str | None = None,
    acting_skill: str | None = None,
    runner: GitRunner = run_git,
    task_resolver: TaskResolver = resolve_task,
    governance_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    task = task_resolver(task_id, bindings)
    governance_policy = governance_policy or load_governance_policy()
    branch, changes = collect_changes(
        include_staged=include_staged,
        include_untracked=include_untracked,
        runner=runner,
    )
    write_scope = [str(value) for value in task["context"]["write_scope"]]
    concrete_scopes = [
        scope for scope in write_scope if is_concrete_scope(scope)
    ]
    declarative_scopes = [
        scope for scope in write_scope if not is_concrete_scope(scope)
    ]

    actual: list[dict[str, Any]] = []
    allowed: list[str] = []
    out_of_scope: list[str] = []
    high_risk: list[dict[str, Any]] = []
    high_risk_undeclared: list[str] = []
    authorization_denied: list[str] = []
    overall_risk = "normal"
    confirmation_required = False
    worktree_recommended = False
    affected_surfaces: set[str] = set()
    rename_count = sum(
        1
        for change in changes
        if any(status.startswith("R") for status in change.statuses)
    )
    manifest = load_manifest() if agent_id else None
    registry = load_registry() if agent_id else None

    for change in changes:
        in_scope = any(
            scope_matches(change.path, scope) for scope in concrete_scopes
        )
        risk = risk_assessment(
            change,
            governance_policy,
            rename_count=rename_count,
        )
        overall_risk = max_risk(overall_risk, risk["risk_level"])
        confirmation_required = (
            confirmation_required or risk["confirmation_required"]
        )
        worktree_recommended = (
            worktree_recommended or risk["worktree_recommended"]
        )
        affected_surfaces.update(risk["affected_surfaces"])
        authorization = (
            check_access(
                governance_policy,
                manifest,
                agent_name=agent_id,
                operation="write",
                raw_path=change.path,
                acting_skill=acting_skill,
                registry=registry,
            )
            if agent_id and manifest is not None and registry is not None
            else None
        )
        if authorization and authorization["status"] != "ALLOW":
            authorization_denied.append(change.path)
        entry = {
            "path": change.path,
            "statuses": sorted(change.statuses),
            "sources": sorted(change.sources),
            "in_scope": in_scope,
            "authorization": authorization,
            **risk,
        }
        actual.append(entry)
        if in_scope:
            allowed.append(change.path)
        else:
            out_of_scope.append(change.path)
        if risk["risk_level"] != "normal":
            high_risk.append(
                {
                    "path": change.path,
                    "risk_level": risk["risk_level"],
                    "reasons": risk["risk_reasons"],
                    "affected_surfaces": risk["affected_surfaces"],
                    "confirmation_required": risk["confirmation_required"],
                    "worktree_recommended": risk["worktree_recommended"],
                    "declared": in_scope,
                }
            )
            if not in_scope:
                high_risk_undeclared.append(change.path)

    warnings: list[str] = []
    if task.get("status") not in {None, "PASS"}:
        warnings.append(
            f"Task resolver status is {task.get('status')}; review task readiness."
        )
    if declarative_scopes:
        warnings.append(
            "Task contains declarative write scopes that cannot be verified "
            "as concrete paths: " + ", ".join(declarative_scopes)
        )

    errors: list[str] = []
    if out_of_scope:
        errors.append(
            "Actual changes exist outside the resolved write scope."
        )
    if high_risk_undeclared:
        errors.append(
            "High-risk changes are not declared by the task write scope."
        )
    if authorization_denied:
        errors.append(
            "Actual changes exceed the effective Agent or acting-Skill authority."
        )

    status = "ERROR" if errors else "WARNING" if warnings else "PASS"
    recommendations = (
        [
            "Stop expanding the current change set; preserve every file.",
            "Choose a better task id or extend the registered task scope.",
            "Transfer out-of-scope work to a separate task or safety branch.",
            "Use an isolated worktree for destructive migration or concurrent high-risk work.",
        ]
        if errors
        else [
            "Review the listed Git changes, then run the task's routed validation.",
            "Use human confirmation for destructive or externally visible actions.",
        ]
    )
    return {
        "status": status,
        "task_id": task_id,
        "task_status": task.get("status", "PASS"),
        "branch": branch,
        "include_staged": include_staged,
        "include_untracked": include_untracked,
        "agent_id": agent_id,
        "acting_skill": acting_skill,
        "write_scope": write_scope,
        "concrete_write_scope": concrete_scopes,
        "declarative_write_scope": declarative_scopes,
        "actual_changes": actual,
        "allowed_files": allowed,
        "out_of_scope_files": out_of_scope,
        "high_risk_files": high_risk,
        "authorization_denied_files": authorization_denied,
        "risk_level": overall_risk,
        "risk_reasons": sorted(
            {
                reason
                for item in high_risk
                for reason in item["reasons"]
            }
        ),
        "affected_surfaces": sorted(affected_surfaces),
        "confirmation_required": confirmation_required,
        "worktree_recommended": worktree_recommended,
        "manual_confirmation_operations": list(
            governance_policy.get("change_risk_policy", {}).get(
                "confirmation_required_operations", []
            )
        ),
        "warnings": warnings,
        "errors": errors,
        "recommended_next_steps": recommendations,
        "destructive_actions_performed": [],
    }


def render_text(payload: dict[str, Any]) -> None:
    print(f"Change scope verification: {payload['status']}")
    print(f"Task: {payload['task_id']}")
    print(f"Branch: {payload['branch']}")
    if payload.get("agent_id"):
        print(f"Agent: {payload['agent_id']}")
    if payload.get("acting_skill"):
        print(f"Acting skill: {payload['acting_skill']}")
    print(f"Risk: {payload['risk_level']}")
    print(f"Confirmation required: {payload['confirmation_required']}")
    print(f"Worktree recommended: {payload['worktree_recommended']}")
    print("Declared write scope:")
    for scope in payload["write_scope"]:
        print(f"  - {scope}")
    print("Actual changes:")
    if not payload["actual_changes"]:
        print("  - none")
    for change in payload["actual_changes"]:
        sources = ", ".join(change["sources"])
        statuses = ", ".join(change["statuses"])
        marker = "allowed" if change["in_scope"] else "OUT-OF-SCOPE"
        authorization = change.get("authorization")
        if authorization and authorization["status"] != "ALLOW":
            marker += "; AUTHORITY-DENIED"
        print(f"  - {change['path']} [{sources}; {statuses}] {marker}")
    if payload["high_risk_files"]:
        print("High-risk changes:")
        for item in payload["high_risk_files"]:
            marker = "declared" if item["declared"] else "UNDECLARED"
            print(
                f"  - {item['path']} [{item['risk_level']}; {marker}]: "
                f"{', '.join(item['reasons'])}"
            )
    for warning in payload["warnings"]:
        print(f"WARNING: {warning}")
    for error in payload["errors"]:
        print(f"ERROR: {error}")
    print("Next:")
    for step in payload["recommended_next_steps"]:
        print(f"  - {step}")
    print("No files were reverted, deleted, cleaned, staged, or modified.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare actual Git changes with a task's resolved write scope."
    )
    parser.add_argument("task_id")
    parser.add_argument("--bind", action="append", default=[], metavar="NAME=VALUE")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--agent")
    parser.add_argument("--skill")
    parser.add_argument(
        "--include-staged",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--include-untracked",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        payload = verify_changes(
            args.task_id,
            args.bind,
            include_staged=args.include_staged,
            include_untracked=args.include_untracked,
            agent_id=args.agent,
            acting_skill=args.skill,
        )
    except (RuntimeError, KeyError, OSError) as exc:
        payload = {
            "status": "ERROR",
            "task_id": args.task_id,
            "error": str(exc),
            "destructive_actions_performed": [],
        }

    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        if "error" in payload:
            print(f"Change scope verification: ERROR")
            print(f"Task: {payload['task_id']}")
            print(f"ERROR: {payload['error']}")
            print("No files were reverted, deleted, cleaned, staged, or modified.")
        else:
            render_text(payload)

    if payload["status"] == "ERROR":
        return 1
    if payload["status"] == "WARNING" and args.strict:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
