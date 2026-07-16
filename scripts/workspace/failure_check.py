from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence


from scripts.workspace.runtime import WORKSPACE_ROOT
RESOLVER = WORKSPACE_ROOT / "scripts" / "resolve_task_context.py"


def run_resolver(
    task_id: str,
    bindings: list[str],
    include_optional: bool,
) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        str(RESOLVER),
        task_id,
        "--format",
        "json",
        "--no-token-count",
    ]
    for binding in bindings:
        command.extend(["--bind", binding])
    if include_optional:
        command.append("--include-optional")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        command,
        cwd=WORKSPACE_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
    )


def finding_advice(finding: dict[str, Any]) -> str:
    reason = finding.get("reason")
    resource_class = finding.get("resource_class")
    if reason == "missing" and resource_class in {"required", "preloaded"}:
        return "Restore the resource, or intentionally update its canonical registry location."
    if reason == "missing":
        return "Continue only if degraded context is acceptable; record the missing evidence."
    if reason == "ignored":
        return "Correct the task ignore policy or remove this resource from the task contract."
    if reason == "path_escape":
        return "Use a workspace-relative source path; do not search outside the workspace."
    return str(finding.get("action") or "Review the resolver finding before continuing.")


def diagnose_payload(
    payload: dict[str, Any],
    *,
    include_optional: bool,
) -> dict[str, Any]:
    context = payload.get("context", {})
    findings = list(context.get("resource_findings", []))
    errors = list(payload.get("errors", []))
    warnings = list(payload.get("warnings", []))
    unresolved = list(context.get("unresolved_placeholders", []))

    blocking_findings = [
        {**finding, "advice": finding_advice(finding)}
        for finding in findings
        if finding.get("severity") == "ERROR"
    ]
    degraded_findings = [
        {**finding, "advice": finding_advice(finding)}
        for finding in findings
        if finding.get("severity") == "WARNING"
    ]

    if errors or blocking_findings:
        status = "BLOCKED"
        can_continue = False
        summary = "Required task context is incomplete. Stop before editing or execution."
    elif warnings or degraded_findings:
        status = "DEGRADED"
        can_continue = True
        summary = "Only optional context is incomplete. Continue with explicit limitations."
    else:
        status = "READY"
        can_continue = True
        summary = "No active resource failure was found for this task."

    actions: list[str] = []
    for placeholder in unresolved:
        actions.append(f"Provide a binding: --bind {placeholder}=<workspace-relative-value>")
    for finding in [*blocking_findings, *degraded_findings]:
        advice = finding["advice"]
        if advice not in actions:
            actions.append(advice)
    if status == "DEGRADED":
        actions.append("Record assumptions or unavailable evidence in the task result.")
    if not include_optional and status != "BLOCKED":
        actions.append(
            "Optional resources were not checked. Add --include-optional only when the task needs them."
        )

    return {
        "status": status,
        "can_continue": can_continue,
        "task": payload.get("task"),
        "summary": summary,
        "include_optional": include_optional,
        "blocking_findings": blocking_findings,
        "degraded_findings": degraded_findings,
        "unresolved_placeholders": unresolved,
        "resolver_errors": errors,
        "resolver_warnings": warnings,
        "actions": actions,
        "guardrails": [
            "Do not guess replacement paths.",
            "Required failures stop the workflow.",
            "Optional failures allow only visible degraded mode.",
            "Platform projections may diagnose exposure but do not replace source.",
        ],
    }


def render_text(result: dict[str, Any]) -> None:
    task = result.get("task") or {}
    print(f"Failure check: {result['status']}")
    if task.get("id"):
        print(f"Task: {task['id']}")
    print(result["summary"])
    for finding in result["blocking_findings"]:
        print(f"\n[BLOCKING] {finding.get('resource')}")
        print(f"  reason: {finding.get('reason')}")
        print(f"  expected: {finding.get('expected')}")
        print(f"  action: {finding.get('advice')}")
    for finding in result["degraded_findings"]:
        print(f"\n[OPTIONAL] {finding.get('resource')}")
        print(f"  reason: {finding.get('reason')}")
        print(f"  impact: {finding.get('impact')}")
        print(f"  action: {finding.get('advice')}")
    if result["actions"]:
        print("\nNext actions:")
        for action in result["actions"]:
            print(f"- {action}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Explain task resource failures without modifying files."
    )
    parser.add_argument("task_id")
    parser.add_argument("--bind", action="append", default=[], metavar="NAME=VALUE")
    parser.add_argument("--include-optional", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    resolver_result = run_resolver(args.task_id, args.bind, args.include_optional)
    try:
        payload = json.loads(resolver_result.stdout)
    except json.JSONDecodeError:
        output = {
            "status": "ERROR",
            "can_continue": False,
            "summary": resolver_result.stderr.strip() or "Task resolver returned invalid output.",
        }
        print(json.dumps(output, indent=2) if args.format == "json" else output["summary"])
        return 1

    if "error" in payload and "task" not in payload:
        output = {
            "status": "ERROR",
            "can_continue": False,
            "summary": str(payload["error"]),
        }
        print(json.dumps(output, indent=2) if args.format == "json" else output["summary"])
        return 1

    output = diagnose_payload(payload, include_optional=args.include_optional)
    if args.format == "json":
        print(json.dumps(output, indent=2))
    else:
        render_text(output)
    if output["status"] == "READY":
        return 0
    if output["status"] == "DEGRADED":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
