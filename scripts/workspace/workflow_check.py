from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Callable, Sequence

from scripts.workspace.plan_change_surface import resolve_task
from scripts.workspace.task_records import active_registration
from scripts.workspace.verify_change_scope import WORKSPACE_ROOT, verify_changes


CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def run_command(arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(arguments),
        cwd=WORKSPACE_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def check_workflow(
    task_id: str,
    bindings: list[str],
    *,
    record_id: str | None = None,
    include_staged: bool = True,
    include_untracked: bool = True,
    agent_id: str | None = None,
    acting_skill: str | None = None,
    command_runner: CommandRunner = run_command,
) -> dict[str, Any]:
    task = resolve_task(task_id, bindings)
    registration: dict[str, Any] | None = None
    registration_error: str | None = None
    if record_id:
        try:
            registration = active_registration(record_id, "workspace_write")
        except ValueError as error:
            registration_error = str(error)
    else:
        registration_error = "--record-id is required for a mutating workspace task"
    verification = verify_changes(
        task_id,
        bindings,
        include_staged=include_staged,
        include_untracked=include_untracked,
        agent_id=agent_id,
        acting_skill=acting_skill,
        task_resolver=lambda *_: task,
        additional_write_scope=[registration["path"]] if registration else [],
    )
    diff_checks = [command_runner(["git", "diff", "--check"])]
    if include_staged:
        diff_checks.append(
            command_runner(["git", "diff", "--cached", "--check"])
        )
    diff_check_passed = all(check.returncode == 0 for check in diff_checks)
    diff_check_output = "\n".join(
        output
        for check in diff_checks
        if (output := (check.stdout.strip() or check.stderr.strip()))
    )

    errors = list(verification.get("errors", []))
    warnings = list(verification.get("warnings", []))
    if registration_error:
        errors.append(registration_error)
    if not diff_check_passed:
        errors.append(
            diff_check_output or "git diff --check failed"
        )

    status = "ERROR" if errors else "WARNING" if warnings else "PASS"
    actual_changes = verification.get("actual_changes", [])
    return {
        "status": status,
        "task_id": task_id,
        "record_id": record_id,
        "registration": registration,
        "branch": verification.get("branch"),
        "agent_id": agent_id,
        "acting_skill": acting_skill,
        "risk_level": verification.get("risk_level", "normal"),
        "risk_reasons": verification.get("risk_reasons", []),
        "affected_surfaces": verification.get("affected_surfaces", []),
        "confirmation_required": verification.get(
            "confirmation_required", False
        ),
        "worktree_recommended": verification.get(
            "worktree_recommended", False
        ),
        "scope_verification": verification,
        "diff_check": {
            "status": "PASS" if diff_check_passed else "ERROR",
            "output": diff_check_output,
        },
        "validation_commands": task["context"].get("validation", []),
        "validation_commands_executed": False,
        "actual_change_count": len(actual_changes),
        "ready_to_commit": status == "PASS" and bool(actual_changes),
        "warnings": warnings,
        "errors": errors,
        "next_steps": (
            verification["recommended_next_steps"]
            if status == "ERROR"
            else [
                "Run only the task validation commands relevant to the change.",
                "Inspect git diff before staging or committing.",
                (
                    "Obtain explicit user confirmation for destructive, migration, "
                    "external-environment, projection, or history-rewrite operations."
                ),
            ]
        ),
        "actions_performed": [
            "resolved task context",
            "read Git change state",
            "verified task write scope",
            "ran git diff --check",
            "checked active task registration",
        ],
        "write_actions_performed": [],
    }


def render_text(payload: dict[str, Any]) -> None:
    print(f"Workflow check: {payload['status']}")
    print(f"Task: {payload['task_id']}")
    print(f"Task record: {payload.get('record_id') or 'missing'}")
    print(f"Branch: {payload['branch']}")
    if payload.get("agent_id"):
        print(f"Agent: {payload['agent_id']}")
    if payload.get("acting_skill"):
        print(f"Acting skill: {payload['acting_skill']}")
    print(f"Risk: {payload['risk_level']}")
    print(f"Confirmation required: {payload['confirmation_required']}")
    print(f"Worktree recommended: {payload['worktree_recommended']}")
    print(f"Scope verification: {payload['scope_verification']['status']}")
    print(f"Git diff check: {payload['diff_check']['status']}")
    print(f"Actual changes: {payload['actual_change_count']}")
    print(f"Ready to commit: {payload['ready_to_commit']}")
    print("Task validation commands (not executed):")
    for command in payload["validation_commands"]:
        print(f"  - {command}")
    for warning in payload["warnings"]:
        print(f"WARNING: {warning}")
    for error in payload["errors"]:
        print(f"ERROR: {error}")
    print("Next:")
    for step in payload["next_steps"]:
        print(f"  - {step}")
    print("No files or Git state were modified.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a read-only pre-commit workflow check for one task."
    )
    parser.add_argument("task_id")
    parser.add_argument("--record-id", required=True)
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
        payload = check_workflow(
            args.task_id,
            args.bind,
            record_id=args.record_id,
            include_staged=args.include_staged,
            include_untracked=args.include_untracked,
            agent_id=args.agent,
            acting_skill=args.skill,
        )
    except (RuntimeError, KeyError, OSError, ValueError) as exc:
        payload = {
            "status": "ERROR",
            "task_id": args.task_id,
            "error": str(exc),
            "write_actions_performed": [],
        }

    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    elif "error" in payload:
        print("Workflow check: ERROR")
        print(f"Task: {payload['task_id']}")
        print(f"ERROR: {payload['error']}")
        print("No files or Git state were modified.")
    else:
        render_text(payload)

    if payload["status"] == "ERROR":
        return 1
    if payload["status"] == "WARNING" and args.strict:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
