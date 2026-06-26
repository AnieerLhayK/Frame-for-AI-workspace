from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = WORKSPACE_ROOT / "scripts"


def run_command(command: Sequence[str]) -> int:
    return subprocess.run(list(command), cwd=WORKSPACE_ROOT, check=False).returncode


def resolver_command(args: argparse.Namespace, *, strict_budget: bool = False) -> list[str]:
    command = [
        sys.executable,
        str(SCRIPTS_DIR / "resolve_task_context.py"),
    ]

    if args.action == "list":
        command.append("--list-prompts" if args.command == "prompt" else "--list")
    elif args.action == "resolve":
        command.append(args.task_id)
    elif args.action == "show":
        command.extend(["--prompt-id", args.prompt_id])
    else:
        raise ValueError(f"Unsupported resolver action: {args.action}")

    command.extend(["--format", args.format])
    for binding in getattr(args, "bind", []):
        command.extend(["--bind", binding])
    if getattr(args, "include_optional", False):
        command.append("--include-optional")
    if getattr(args, "include_template", False):
        command.append("--include-template")
    if getattr(args, "no_token_count", False):
        command.append("--no-token-count")
    if strict_budget or getattr(args, "strict_budget", False):
        command.append("--strict-budget")
    if getattr(args, "encoding", None):
        command.extend(["--encoding", args.encoding])
    return command


def add_output_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=("text", "json"), default="text")


def add_resolution_options(parser: argparse.ArgumentParser) -> None:
    add_output_options(parser)
    parser.add_argument("--bind", action="append", default=[], metavar="NAME=VALUE")
    parser.add_argument("--include-optional", action="store_true")
    parser.add_argument("--include-template", action="store_true")
    parser.add_argument("--no-token-count", action="store_true")
    parser.add_argument("--strict-budget", action="store_true")
    parser.add_argument("--encoding")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="workspace",
        description="Unified entry point for existing workspace maintenance tools.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    task_parser = commands.add_parser("task", help="List or resolve registered tasks.")
    task_commands = task_parser.add_subparsers(dest="action", required=True)
    task_list = task_commands.add_parser("list", help="List exact task ids.")
    add_output_options(task_list)
    task_resolve = task_commands.add_parser("resolve", help="Resolve bounded task context.")
    task_resolve.add_argument("task_id")
    add_resolution_options(task_resolve)

    prompt_parser = commands.add_parser("prompt", help="List or resolve registered prompts.")
    prompt_commands = prompt_parser.add_subparsers(dest="action", required=True)
    prompt_list = prompt_commands.add_parser("list", help="List prompt ids.")
    add_output_options(prompt_list)
    prompt_show = prompt_commands.add_parser("show", help="Resolve one prompt.")
    prompt_show.add_argument("prompt_id")
    prompt_show.add_argument("--include-template", action="store_true")
    prompt_show.add_argument("--no-token-count", action="store_true")
    prompt_show.add_argument("--encoding")
    add_output_options(prompt_show)

    preflight = commands.add_parser(
        "preflight",
        help="Resolve a task and fail when its token budget is not PASS.",
    )
    preflight.set_defaults(action="resolve")
    preflight.add_argument("task_id")
    add_resolution_options(preflight)

    bootstrap = commands.add_parser(
        "bootstrap",
        help="Discover workspace_manifest.yaml by bounded parent lookup.",
    )
    bootstrap.add_argument("--start", default=".")
    bootstrap.add_argument("--max-parent-depth", type=int, default=8)
    bootstrap.add_argument("--print-json", action="store_true")

    health = commands.add_parser(
        "health",
        help="Run live read-only workspace health checks.",
    )
    health.add_argument("--with-tests", action="store_true")
    health.add_argument("--format", choices=("text", "json"), default="text")

    summary = commands.add_parser(
        "summary",
        help="Show live workspace version and governance facts.",
    )
    summary.add_argument("--recent", type=int, default=5)
    summary.add_argument("--format", choices=("text", "json"), default="text")

    sessions = commands.add_parser("sessions", help="Audit conversation continuity after path migrations.")
    session_commands = sessions.add_subparsers(dest="action", required=True)
    session_audit = session_commands.add_parser(
        "audit",
        help="Verify live Claude/OpenCode sessions and external migration backups.",
    )
    session_audit.add_argument("--migration-id")
    session_audit.add_argument("--format", choices=("text", "json"), default="text")

    agent = commands.add_parser(
        "agent",
        help="Inspect agent authority, create change requests, or validate leases.",
    )
    agent_commands = agent.add_subparsers(dest="action", required=True)
    agent_status = agent_commands.add_parser("status", help="Show agent roles and surface classes.")
    agent_status.add_argument("--format", choices=("text", "json"), default="text")
    agent_list = agent_commands.add_parser("list", help="List agent registration summaries.")
    agent_list.add_argument("--format", choices=("text", "json"), default="text")
    agent_show = agent_commands.add_parser("show", help="Show one resolved agent registration.")
    agent_show.add_argument("agent_id")
    agent_show.add_argument("--format", choices=("text", "json"), default="text")
    agent_validate = agent_commands.add_parser("validate", help="Validate one agent registration.")
    agent_validate.add_argument("agent_id")
    agent_validate.add_argument("--format", choices=("text", "json"), default="text")
    agent_doctor = agent_commands.add_parser(
        "doctor",
        help="Diagnose agent registry, policy, manifest, platform, and storage consistency.",
    )
    agent_doctor.add_argument("agent_id")
    agent_doctor.add_argument("--format", choices=("text", "json"), default="text")
    agent_check = agent_commands.add_parser("check", help="Check an agent operation against one path.")
    agent_check.add_argument("--agent", required=True)
    agent_check.add_argument("--operation", choices=("read", "write"), default="write")
    agent_check.add_argument("--path", required=True)
    agent_check.add_argument("--skill")
    agent_check.add_argument("--lease")
    agent_check.add_argument("--format", choices=("text", "json"), default="text")
    agent_request = agent_commands.add_parser("request", help="Create a reviewable change request.")
    agent_request.add_argument("--agent", required=True)
    agent_request.add_argument(
        "--mode",
        choices=("review_only", "temporary_lease", "worktree"),
        default="review_only",
    )
    agent_request.add_argument("--summary", required=True)
    agent_request.add_argument("--path", action="append", default=[])
    agent_request.add_argument("--output")
    agent_request.add_argument("--format", choices=("text", "json"), default="text")
    agent_lease = agent_commands.add_parser("lease", help="Manage temporary capability leases.")
    lease_commands = agent_lease.add_subparsers(dest="lease_action", required=True)
    lease_validate = lease_commands.add_parser("validate", help="Validate an external lease file.")
    lease_validate.add_argument("lease_file")
    lease_validate.add_argument("--format", choices=("text", "json"), default="text")

    skill = commands.add_parser("skill", help="Create, inspect, validate, or expose skills.")
    skill_commands = skill.add_subparsers(dest="action", required=True)
    skill_init = skill_commands.add_parser("init", help="Create an unregistered skill source scaffold.")
    skill_init.add_argument("skill_id")
    skill_init.add_argument("--source-path", required=True)
    skill_init.add_argument("--description", required=True)
    skill_init.add_argument("--format", choices=("text", "json"), default="text")
    skill_validate = skill_commands.add_parser("validate", help="Validate a registered id or source path.")
    skill_validate.add_argument("target")
    skill_validate.add_argument("--format", choices=("text", "json"), default="text")
    skill_list = skill_commands.add_parser("list", help="List manifest skills and projection states.")
    skill_list.add_argument("--platform")
    skill_list.add_argument("--format", choices=("text", "json"), default="text")
    skill_expose = skill_commands.add_parser(
        "expose",
        help="Preview or create one manifest-declared platform projection.",
    )
    skill_expose.add_argument("skill_id")
    skill_expose.add_argument("--platform")
    skill_expose.add_argument("--apply", action="store_true")
    skill_expose.add_argument("--format", choices=("text", "json"), default="text")

    launcher = commands.add_parser("launcher", help="Manage the short workspace command.")
    launcher.add_argument("action", choices=("install", "status", "uninstall"))
    launcher.add_argument("--install-dir")
    launcher.add_argument("--dry-run", action="store_true")
    launcher.add_argument("--format", choices=("text", "json"), default="text")

    failure = commands.add_parser("failure", help="Explain task resource failures.")
    failure_commands = failure.add_subparsers(dest="action", required=True)
    failure_check = failure_commands.add_parser(
        "check",
        help="Classify task resources as ready, degraded, or blocked.",
    )
    failure_check.add_argument("task_id")
    failure_check.add_argument("--bind", action="append", default=[], metavar="NAME=VALUE")
    failure_check.add_argument("--include-optional", action="store_true")
    failure_check.add_argument("--format", choices=("text", "json"), default="text")

    validate = commands.add_parser("validate", help="Run an existing workspace validator.")
    validate_commands = validate.add_subparsers(dest="target", required=True)
    validate_commands.add_parser(
        "manifest",
        help="Validate the manifest and refresh its snapshot report.",
    )
    validate_commands.add_parser(
        "protocols",
        help="Validate shared protocols and refresh their snapshot report.",
    )
    validate_links = validate_commands.add_parser(
        "links",
        help="Check platform projections without changing them.",
    )
    validate_links.add_argument("--manifest-path")

    knowledge = commands.add_parser("knowledge", help="Find bounded knowledge entry points.")
    knowledge_commands = knowledge.add_subparsers(dest="action", required=True)
    knowledge_list = knowledge_commands.add_parser("list", help="List knowledge topics.")
    knowledge_list.add_argument("--format", choices=("text", "json"), default="text")
    knowledge_validate = knowledge_commands.add_parser(
        "validate",
        help="Check every indexed knowledge path.",
    )
    knowledge_validate.add_argument("--format", choices=("text", "json"), default="text")
    knowledge_find = knowledge_commands.add_parser("find", help="Find topics by phrase or alias.")
    knowledge_find.add_argument("query")
    knowledge_find.add_argument("--limit", type=int, default=3)
    knowledge_find.add_argument(
        "--layer",
        choices=(
            "project_context",
            "shared",
            "workspace_engineering",
            "skill_engineering",
            "usage_guides",
            "manifest",
            "tooling",
            "documentation",
        ),
    )
    knowledge_find.add_argument("--format", choices=("text", "json"), default="text")

    changes = commands.add_parser("changes", help="Plan or verify task change surfaces.")
    change_commands = changes.add_subparsers(dest="action", required=True)
    change_plan = change_commands.add_parser(
        "plan",
        help="Rank candidate file sets without modifying them.",
    )
    change_plan.add_argument("task_id")
    change_plan.add_argument(
        "--intent",
        choices=(
            "behavior",
            "metadata",
            "exposure",
            "routing",
            "tooling",
            "policy",
            "documentation",
            "report",
            "migration",
            "architecture",
            "general",
        ),
        required=True,
    )
    change_plan.add_argument("--goal")
    change_plan.add_argument("--bind", action="append", default=[], metavar="NAME=VALUE")
    change_plan.add_argument("--option", action="append", default=[])
    change_plan.add_argument("--format", choices=("text", "json"), default="text")
    change_verify = change_commands.add_parser(
        "verify",
        help="Compare actual Git changes with a task's resolved write scope.",
    )
    change_verify.add_argument("task_id")
    change_verify.add_argument("--bind", action="append", default=[], metavar="NAME=VALUE")
    change_verify.add_argument("--format", choices=("text", "json"), default="text")
    change_verify.add_argument("--strict", action="store_true")
    change_verify.add_argument("--agent")
    change_verify.add_argument("--skill")
    change_verify.add_argument(
        "--include-staged",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    change_verify.add_argument(
        "--include-untracked",
        action=argparse.BooleanOptionalAction,
        default=True,
    )

    workflow = commands.add_parser(
        "workflow",
        help="Run a read-only task workflow check before commit.",
    )
    workflow_commands = workflow.add_subparsers(dest="action", required=True)
    workflow_check = workflow_commands.add_parser(
        "check",
        help="Resolve, verify scope, run git diff --check, and list validation.",
    )
    workflow_check.add_argument("task_id")
    workflow_check.add_argument("--bind", action="append", default=[], metavar="NAME=VALUE")
    workflow_check.add_argument("--format", choices=("text", "json"), default="text")
    workflow_check.add_argument("--strict", action="store_true")
    workflow_check.add_argument("--agent")
    workflow_check.add_argument("--skill")
    workflow_check.add_argument(
        "--include-staged",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    workflow_check.add_argument(
        "--include-untracked",
        action=argparse.BooleanOptionalAction,
        default=True,
    )

    reports = commands.add_parser("reports", help="Inspect or refresh snapshot reports.")
    report_commands = reports.add_subparsers(dest="action", required=True)
    report_status = report_commands.add_parser(
        "status",
        help="Check report freshness without writing files.",
    )
    report_status.add_argument(
        "--report-id",
        choices=("manifest-validation", "protocol-validation", "workspace"),
        action="append",
        default=[],
    )
    report_status.add_argument("--format", choices=("text", "json"), default="text")
    report_status.add_argument("--strict", action="store_true")
    report_refresh = report_commands.add_parser(
        "refresh",
        help="Explicitly regenerate one current-state report group.",
    )
    report_refresh.add_argument(
        "report_id",
        choices=("manifest-validation", "protocol-validation", "workspace", "all-current"),
    )

    return parser


def dispatch(args: argparse.Namespace) -> int:
    if args.command in {"task", "prompt"}:
        return run_command(resolver_command(args))
    if args.command == "preflight":
        return run_command(resolver_command(args, strict_budget=True))
    if args.command == "bootstrap":
        start_path = str(Path(args.start).resolve())
        command = [
            sys.executable,
            str(SCRIPTS_DIR / "bootstrap_workspace.py"),
            "--start",
            start_path,
            "--max-parent-depth",
            str(args.max_parent_depth),
        ]
        if args.print_json:
            command.append("--print-json")
        return run_command(command)
    if args.command == "health":
        command = [sys.executable, str(SCRIPTS_DIR / "workspace_health.py")]
        if args.with_tests:
            command.append("--with-tests")
        command.extend(["--format", args.format])
        return run_command(command)
    if args.command == "summary":
        return run_command(
            [
                sys.executable,
                str(SCRIPTS_DIR / "workspace_summary.py"),
                "--recent",
                str(max(1, args.recent)),
                "--format",
                args.format,
            ]
        )
    if args.command == "sessions":
        command = [
            sys.executable,
            str(SCRIPTS_DIR / "session_continuity.py"),
            "--format",
            args.format,
        ]
        if args.migration_id:
            command.extend(["--migration-id", args.migration_id])
        return run_command(command)
    if args.command == "agent":
        command = [
            sys.executable,
            str(SCRIPTS_DIR / "agent_governance.py"),
            args.action,
        ]
        if args.action == "check":
            command.extend(
                [
                    "--agent",
                    args.agent,
                    "--operation",
                    args.operation,
                    "--path",
                    args.path,
                ]
            )
            if args.skill:
                command.extend(["--skill", args.skill])
            if args.lease:
                command.extend(["--lease", args.lease])
        elif args.action == "request":
            command.extend(
                [
                    "--agent",
                    args.agent,
                    "--mode",
                    args.mode,
                    "--summary",
                    args.summary,
                ]
            )
            for path in args.path:
                command.extend(["--path", path])
            if args.output:
                command.extend(["--output", args.output])
        elif args.action in {"show", "validate", "doctor"}:
            command.append(args.agent_id)
        elif args.action == "lease":
            command.extend([args.lease_action, args.lease_file])
        command.extend(["--format", args.format])
        return run_command(command)
    if args.command == "skill":
        command = [
            sys.executable,
            str(SCRIPTS_DIR / "skill_lifecycle.py"),
            args.action,
        ]
        if args.action == "init":
            command.extend(
                [
                    args.skill_id,
                    "--source-path",
                    args.source_path,
                    "--description",
                    args.description,
                ]
            )
        elif args.action == "validate":
            command.append(args.target)
        elif args.action == "list":
            if args.platform:
                command.extend(["--platform", args.platform])
        else:
            command.append(args.skill_id)
            if args.platform:
                command.extend(["--platform", args.platform])
            if args.apply:
                command.append("--apply")
        command.extend(["--format", args.format])
        return run_command(command)
    if args.command == "launcher":
        command = [
            sys.executable,
            str(SCRIPTS_DIR / "workspace_launcher.py"),
            args.action,
            "--format",
            args.format,
        ]
        if args.install_dir:
            command.extend(["--install-dir", args.install_dir])
        if args.dry_run:
            command.append("--dry-run")
        return run_command(command)
    if args.command == "failure":
        command = [
            sys.executable,
            str(SCRIPTS_DIR / "failure_check.py"),
            args.task_id,
            "--format",
            args.format,
        ]
        for binding in args.bind:
            command.extend(["--bind", binding])
        if args.include_optional:
            command.append("--include-optional")
        return run_command(command)
    if args.command == "validate":
        if args.target == "manifest":
            return run_command([sys.executable, str(SCRIPTS_DIR / "validate_manifest.py")])
        if args.target == "protocols":
            return run_command([sys.executable, str(SCRIPTS_DIR / "validate_protocols.py")])
        command = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(SCRIPTS_DIR / "check_links.ps1"),
        ]
        if args.manifest_path:
            command.extend(["-ManifestPath", args.manifest_path])
        return run_command(command)
    if args.command == "knowledge":
        command = [sys.executable, str(SCRIPTS_DIR / "find_knowledge.py")]
        if args.action == "list":
            command.append("--list")
        elif args.action == "validate":
            command.append("--validate")
        else:
            command.extend(["--query", args.query, "--limit", str(args.limit)])
            if args.layer:
                command.extend(["--layer", args.layer])
        command.extend(["--format", args.format])
        return run_command(command)
    if args.command == "changes":
        if args.action == "verify":
            command = [
                sys.executable,
                str(SCRIPTS_DIR / "verify_change_scope.py"),
                args.task_id,
                "--format",
                args.format,
            ]
            for binding in args.bind:
                command.extend(["--bind", binding])
            if args.strict:
                command.append("--strict")
            if args.agent:
                command.extend(["--agent", args.agent])
            if args.skill:
                command.extend(["--skill", args.skill])
            if not args.include_staged:
                command.append("--no-include-staged")
            if not args.include_untracked:
                command.append("--no-include-untracked")
            return run_command(command)
        command = [
            sys.executable,
            str(SCRIPTS_DIR / "plan_change_surface.py"),
            args.task_id,
            "--intent",
            args.intent,
            "--format",
            args.format,
        ]
        if args.goal:
            command.extend(["--goal", args.goal])
        for binding in args.bind:
            command.extend(["--bind", binding])
        for option in args.option:
            command.extend(["--option", option])
        return run_command(command)
    if args.command == "workflow":
        command = [
            sys.executable,
            str(SCRIPTS_DIR / "workflow_check.py"),
            args.task_id,
            "--format",
            args.format,
        ]
        for binding in args.bind:
            command.extend(["--bind", binding])
        if args.strict:
            command.append("--strict")
        if args.agent:
            command.extend(["--agent", args.agent])
        if args.skill:
            command.extend(["--skill", args.skill])
        if not args.include_staged:
            command.append("--no-include-staged")
        if not args.include_untracked:
            command.append("--no-include-untracked")
        return run_command(command)
    if args.command == "reports":
        if args.action == "status":
            command = [sys.executable, str(SCRIPTS_DIR / "report_status.py")]
            for report_id in args.report_id:
                command.extend(["--report-id", report_id])
            command.extend(["--format", args.format])
            if args.strict:
                command.append("--strict")
            return run_command(command)

        refresh_commands = {
            "manifest-validation": [
                sys.executable,
                str(SCRIPTS_DIR / "validate_manifest.py"),
            ],
            "protocol-validation": [
                sys.executable,
                str(SCRIPTS_DIR / "validate_protocols.py"),
            ],
            "workspace": [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(SCRIPTS_DIR / "sync_report.ps1"),
            ],
        }
        targets = (
            tuple(refresh_commands)
            if args.report_id == "all-current"
            else (args.report_id,)
        )
        for target in targets:
            return_code = run_command(refresh_commands[target])
            if return_code != 0:
                return return_code
        return 0
    raise ValueError(f"Unsupported command: {args.command}")


def main() -> int:
    return dispatch(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
