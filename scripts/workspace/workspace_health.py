from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

import yaml

from scripts.workspace.agent_governance import absolute_path_is_within, load_manifest
from scripts.workspace.runtime import SCRIPTS_ROOT as SCRIPTS_DIR
from scripts.workspace.runtime import WORKSPACE_ROOT
WORKSPACE_SOURCE_ROOT = str(
    load_manifest().get("workspace", {}).get("source_of_truth") or WORKSPACE_ROOT
)
FORBIDDEN_ROOT_RUNTIME_PATHS = (
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
)
FORBIDDEN_ROOT_PROJECT_PATHS = ("claude",)
REQUIRED_CLAUDE_BOUNDARY_PATHS = (
    "AGENTS.md",
    ".claude/project-boundary.json",
    ".claude/rules/workspace-boundary.md",
    ".claude/settings.json",
    ".claude/hooks/workspace_boundary_guard.ps1",
)
HERMES_HOME = Path(os.environ.get("HERMES_HOME", r"${DATA_ROOT}/hermes"))
HERMES_GUARD_SCRIPT = SCRIPTS_DIR / "workspace" / "hermes_workspace_guard.py"


def _workspace_source_path(*parts: str) -> str:
    root = WORKSPACE_SOURCE_ROOT.replace("/", "\\").rstrip("\\")
    return "\\".join((root, *parts))


REQUIRED_AGENT_READ_ROOTS = {
    _workspace_source_path("packages", "character-system", "shared").casefold(),
    _workspace_source_path(
        "packages", "character-system", "reports", "runtime-loop"
    ).casefold(),
}
OPENCODE_CONFIG = WORKSPACE_ROOT / "opencode.json"
OPENCODE_GUARD = WORKSPACE_ROOT / ".opencode" / "plugins" / "workspace-governance.js"
AGENT_REGISTRY = WORKSPACE_ROOT / "shared" / "governance" / "agent_registry.yaml"



@dataclass
class CheckResult:
    check_id: str
    status: str
    summary: str
    details: dict[str, Any] | None = None


def run_process(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return subprocess.run(
        list(command),
        cwd=WORKSPACE_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
    )


def parse_json_output(result: subprocess.CompletedProcess[str]) -> dict[str, Any] | None:
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def check_bootstrap(
    runner: Callable[[Sequence[str]], subprocess.CompletedProcess[str]] = run_process,
) -> CheckResult:
    result = runner(
        [
            sys.executable,
            "-m",
            "scripts.workspace.bootstrap_workspace",
            "--start",
            str(WORKSPACE_ROOT),
            "--print-json",
        ]
    )
    payload = parse_json_output(result)
    if result.returncode != 0 or payload is None:
        return CheckResult("bootstrap", "ERROR", "Workspace discovery failed.")
    source_root = Path(str(payload.get("source_of_truth", "")))
    if source_root.resolve() != WORKSPACE_ROOT.resolve():
        return CheckResult(
            "bootstrap",
            "FAIL",
            "Discovered source root does not match this workspace.",
            payload,
        )
    return CheckResult("bootstrap", "PASS", "Workspace manifest and source root resolved.", payload)


def check_knowledge(
    runner: Callable[[Sequence[str]], subprocess.CompletedProcess[str]] = run_process,
) -> CheckResult:
    result = runner(
        [
            sys.executable,
            "-m", "scripts.workspace.knowledge_registry",
            "--validate",
            "--format",
            "json",
        ]
    )
    payload = parse_json_output(result)
    if payload is None:
        return CheckResult("knowledge", "ERROR", "Knowledge validation returned invalid output.")
    if result.returncode != 0 or payload.get("status") != "PASS":
        return CheckResult("knowledge", "FAIL", "Knowledge registry has missing entries.", payload)
    return CheckResult(
        "knowledge",
        "PASS",
        f"{payload.get('topic_count', 0)} topics and {payload.get('entry_count', 0)} entries are valid.",
        payload,
    )


def check_reports(
    runner: Callable[[Sequence[str]], subprocess.CompletedProcess[str]] = run_process,
) -> CheckResult:
    result = runner(
        [
            sys.executable,
            "-m", "scripts.reporting.report_status",
            "--strict",
            "--format",
            "json",
        ]
    )
    payload = parse_json_output(result)
    if payload is None:
        return CheckResult("reports", "ERROR", "Report status returned invalid output.")
    reports = payload.get("reports", [])
    stale = [report.get("report_id") for report in reports if report.get("status") != "FRESH"]
    if result.returncode != 0 or stale:
        names = ", ".join(str(name) for name in stale) or "unknown"
        return CheckResult("reports", "FAIL", f"Stale or missing report groups: {names}.", payload)
    return CheckResult("reports", "PASS", f"{len(reports)} current report groups are fresh.", payload)


def check_links(
    runner: Callable[[Sequence[str]], subprocess.CompletedProcess[str]] = run_process,
) -> CheckResult:
    result = runner(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(WORKSPACE_ROOT / "scripts" / "validation" / "check_links.ps1"),
        ]
    )
    if result.returncode != 0:
        return CheckResult("links", "FAIL", "One or more platform projections are invalid.")
    return CheckResult("links", "PASS", "Manifest projections and shared uniqueness passed.")


def check_hygiene(root: Path = WORKSPACE_ROOT) -> CheckResult:
    caches = [name for name in FORBIDDEN_ROOT_RUNTIME_PATHS if (root / name).exists()]
    projects = [name for name in FORBIDDEN_ROOT_PROJECT_PATHS if (root / name).exists()]
    missing_boundaries = [name for name in REQUIRED_CLAUDE_BOUNDARY_PATHS if not (root / name).exists()]
    if caches or projects or missing_boundaries:
        findings = caches + projects + missing_boundaries
        return CheckResult(
            "hygiene",
            "FAIL",
            f"Workspace boundary or hygiene issue: {', '.join(findings)}.",
            {
                "runtime_caches": caches,
                "external_project_directories": projects,
                "missing_claude_boundaries": missing_boundaries,
                "action": "Remove runtime caches or external projects and restore tracked Claude boundary files.",
            },
        )
    return CheckResult("hygiene", "PASS", "Workspace root and Claude project boundary are clean.")


def check_hermes_guard(
    config_path: Path | None = None,
    allowlist_path: Path | None = None,
) -> CheckResult:
    config_path = config_path or HERMES_HOME / "config.yaml"
    allowlist_path = allowlist_path or HERMES_HOME / "shell-hooks-allowlist.json"
    findings: list[str] = []
    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8-sig")) or {}
        allowlist = json.loads(allowlist_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return CheckResult(
            "hermes-guard",
            "FAIL",
            "Hermes runtime governance configuration could not be read.",
            {"error": str(exc)},
        )

    hooks = config.get("hooks", {})
    required_events = ("pre_tool_call", "post_tool_call", "pre_llm_call")
    configured_commands: dict[str, str] = {}
    configured_entries: dict[str, dict[str, Any]] = {}
    for event in required_events:
        entries = hooks.get(event, [])
        entry = next(
            (
                entry
                for entry in entries
                if isinstance(entry, dict)
                and "-m scripts.workspace.hermes_workspace_guard" in str(entry.get("command", ""))
            ),
            None,
        )
        if entry is None:
            findings.append(f"missing {event} workspace guard hook")
        else:
            command = str(entry.get("command", ""))
            configured_commands[event] = command
            configured_entries[event] = entry

    approvals = {
        (str(entry.get("event", "")), str(entry.get("command", ""))): entry
        for entry in allowlist.get("approvals", [])
        if isinstance(entry, dict)
    }
    expected_mtime = (
        datetime.fromtimestamp(
            HERMES_GUARD_SCRIPT.stat().st_mtime,
            tz=timezone.utc,
        )
        .isoformat()
        .replace("+00:00", "Z")
        if HERMES_GUARD_SCRIPT.exists()
        else None
    )
    for event, command in configured_commands.items():
        approval = approvals.get((event, command))
        if approval is None:
            findings.append(f"{event} workspace guard hook is not allowlisted")
        elif approval.get("script_mtime_at_approval") != expected_mtime:
            findings.append(
                f"{event} workspace guard hook changed after approval"
            )

    pre_tool_matcher = str(
        configured_entries.get("pre_tool_call", {}).get("matcher", "")
    )
    required_pre_tool_matches = {
        "patch",
        "write_file",
        "terminal",
        "skill_manage",
        "execute_code",
        "process",
        "mcp_.*",
    }
    configured_matches = {
        value.strip() for value in pre_tool_matcher.split("|") if value.strip()
    }
    if not required_pre_tool_matches.issubset(configured_matches):
        findings.append("Hermes pre_tool_call matcher does not cover all guarded tools")

    terminal_cwd = str(config.get("terminal", {}).get("cwd", WORKSPACE_ROOT))
    if absolute_path_is_within(terminal_cwd, WORKSPACE_SOURCE_ROOT):
        findings.append("Hermes terminal cwd still points inside the workspace")

    filesystem = config.get("mcp_servers", {}).get("filesystem", {})
    roots = {
        str(value).replace("/", "\\").rstrip("\\").casefold()
        for value in filesystem.get("args", [])
    }
    if {r"d:\ai", r"d:\dev"} & roots:
        findings.append("Hermes filesystem MCP still exposes a broad drive root")
    if not REQUIRED_AGENT_READ_ROOTS.issubset(roots):
        findings.append(
            "Hermes filesystem MCP is missing character runtime-loop read roots"
        )
    excluded = {
        str(value)
        for value in filesystem.get("tools", {}).get("exclude", [])
    }
    required_exclusions = {
        "write_file",
        "edit_file",
        "create_directory",
        "move_file",
    }
    if not required_exclusions.issubset(excluded):
        findings.append("Hermes filesystem MCP mutation tools are not excluded")

    if not config.get("skills", {}).get("guard_agent_created", False):
        findings.append("Hermes agent-created skill guard is disabled")
    if not HERMES_GUARD_SCRIPT.exists():
        findings.append("tracked Hermes workspace guard script is missing")

    if findings:
        return CheckResult(
            "hermes-guard",
            "FAIL",
            "Hermes runtime governance is not fully enforced.",
            {"findings": findings},
        )
    return CheckResult(
        "hermes-guard",
        "PASS",
        "Hermes cognition hooks, write guard, and MCP restrictions are active.",
    )


def _normalized_windows_roots(values: Sequence[Any]) -> set[str]:
    return {
        str(value).replace("/", "\\").rstrip("\\").casefold()
        for value in values
        if isinstance(value, str)
    }


def check_platform_agent_guards(
    opencode_path: Path | None = None,
    opencode_guard_path: Path | None = None,
    registry_path: Path | None = None,
) -> CheckResult:
    opencode_path = opencode_path or OPENCODE_CONFIG
    opencode_guard_path = opencode_guard_path or OPENCODE_GUARD
    registry_path = registry_path or AGENT_REGISTRY
    findings: list[str] = []
    try:
        opencode = json.loads(opencode_path.read_text(encoding="utf-8-sig"))
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8-sig")) or {}
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return CheckResult(
            "platform-agent-guards",
            "FAIL",
            "OpenCode workspace governance configuration could not be read.",
            {"error": str(exc)},
        )

    if "./.opencode/plugins/workspace-governance.js" not in opencode.get("plugin", []):
        findings.append("OpenCode project governance plugin is not configured")
    permission = opencode.get("permission", {})
    if permission.get("edit", {}).get("*") != "deny":
        findings.append("OpenCode edit fallback is not deny")
    if permission.get("bash", {}).get("*") != "deny":
        findings.append("OpenCode bash fallback is not deny")
    if permission.get("external_directory", {}).get("*") != "deny":
        findings.append("OpenCode external directory access is not deny")
    if not opencode_guard_path.exists():
        findings.append("OpenCode project governance plugin is missing")

    agents = registry.get("agents", {})
    for agent_id in ("deepseek-harness", "opencode"):
        entry = agents.get(agent_id, {})
        if entry.get("status") != "active" or entry.get("role") != "record_producer":
            findings.append(f"{agent_id} is not an active record_producer")
    for agent_id, role in (("codex", "structural_maintainer"), ("claude", "development_maintainer")):
        entry = agents.get(agent_id, {})
        if entry.get("status") != "active" or entry.get("role") != role:
            findings.append(f"{agent_id} is not an active {role}")
    if findings:
        return CheckResult(
            "platform-agent-guards",
            "FAIL",
            "DeepSeek Harness/OpenCode workspace governance has drifted.",
            {"findings": findings},
        )
    return CheckResult(
        "platform-agent-guards",
        "PASS",
        "Codex is a structural maintainer; Claude is a development maintainer; DeepSeek Harness and OpenCode are registered record producers.",
    )


def check_deepseek_desktop_contract(workspace_root: Path | None = None) -> CheckResult:
    """Check portable source declarations, not Desktop runtime enforcement."""
    root = workspace_root or WORKSPACE_ROOT
    findings: list[str] = []
    try:
        registry_path = root / "shared/governance/agent_registry.yaml"
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8-sig")) or {}
        agent = registry["agents"]["deepseek-harness"]
        launcher_path = root / "scripts/platform/Start-DeepSeekHarnessDesktop.ps1"
        launcher = launcher_path.read_text(encoding="utf-8-sig")
        if not isinstance(agent, dict):
            raise TypeError("DeepSeek registration must be a mapping")
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
        return CheckResult(
            "deepseek-harness-desktop", "FAIL",
            "DeepSeek Desktop source declarations could not be read.", {"error": str(exc)},
        )
    if agent.get("host", {}).get("kind") != "desktop_app":
        findings.append("DeepSeek host is not registered as Desktop")
    if agent.get("role") != "record_producer" or agent.get("capabilities", {}).get("allow") != []:
        findings.append("Desktop role or additional capabilities drifted")
    if agent.get("active_lease_refs") != []:
        findings.append("Desktop retains a legacy pilot lease reference")
    if "desktop-home" not in launcher or "desktop\\DeepSeek Harness.exe" not in launcher:
        findings.append("Native launcher does not use the fresh managed Desktop paths")
    retired_paths = (
        "scripts/platform/dsh-pilot.cmd",
        "scripts/platform/Start-DeepSeekHarnessWorkspacePilot.ps1",
        "scripts/platform/deepseek-harness-governance/package.json",
    )
    for obsolete in retired_paths:
        if (root / obsolete).exists():
            findings.append(f"Retired source entry still exists: {obsolete}")
    return CheckResult(
        "deepseek-harness-desktop", "FAIL" if findings else "PASS",
        "DeepSeek Desktop source declarations drifted." if findings else
        "Native Desktop entry is declared; no Workspace runtime-enforcement adapter is registered.",
        {"findings": findings, "runtime_enforcement": False},
    )


def _path_is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root.resolve())
        return True
    except ValueError:
        return False


def check_tests(
    runner: Callable[[Sequence[str]], subprocess.CompletedProcess[str]] = run_process,
) -> CheckResult:
    result = runner(
        [
            sys.executable,
            "-m", "scripts.reporting.ci_run",
            "--format",
            "json",
        ]
    )
    payload = parse_json_output(result)
    if payload is None:
        return CheckResult(
            "tests",
            "ERROR",
            "CI test aggregator returned invalid JSON.",
            {
                "stdout_tail": result.stdout[-2000:],
                "stderr_tail": result.stderr[-2000:],
            },
        )
    core_failures = payload.get("core_failures", [])
    infra_failures = payload.get("infra_failures", [])
    if not isinstance(core_failures, list) or not isinstance(infra_failures, list):
        return CheckResult("tests", "ERROR", "CI test aggregator returned invalid failure details.", payload)
    if result.returncode != 0 or payload.get("status") != "PASS" or core_failures:
        return CheckResult(
            "tests",
            "FAIL",
            "Workspace core script tests failed.",
            payload,
        )
    if infra_failures:
        return CheckResult(
            "tests",
            "PASS",
            f"Workspace core tests passed; {len(infra_failures)} infrastructure failure(s) are non-blocking.",
            payload,
        )
    return CheckResult("tests", "PASS", "Workspace script tests passed.", payload)


def run_health(
    *,
    with_tests: bool = False,
    runner: Callable[[Sequence[str]], subprocess.CompletedProcess[str]] = run_process,
    hygiene_checker: Callable[[], CheckResult] = check_hygiene,
    hermes_guard_checker: Callable[[], CheckResult] = check_hermes_guard,
    platform_guard_checker: Callable[[], CheckResult] = check_platform_agent_guards,
) -> dict[str, Any]:
    checks = [
        check_bootstrap(runner),
        check_knowledge(runner),
        check_reports(runner),
        check_links(runner),
        hygiene_checker(),
        hermes_guard_checker(),
        platform_guard_checker(),
        check_deepseek_desktop_contract(),
    ]
    if with_tests:
        checks.append(check_tests(runner))

    statuses = {check.status for check in checks}
    if "ERROR" in statuses:
        status = "ERROR"
    elif "FAIL" in statuses:
        status = "NEEDS_ATTENTION"
    else:
        status = "PASS"
    return {
        "status": status,
        "workspace_root": str(WORKSPACE_ROOT),
        "with_tests": with_tests,
        "checks": [asdict(check) for check in checks],
        "note": "This command is read-only and does not refresh reports or modify source files.",
    }


HEALTH_GROUPS = (
    (
        "Core Workspace",
        (
            ("bootstrap", "Manifest/source root"),
            ("knowledge", "Knowledge index"),
            ("links", "Platform links"),
        ),
    ),
    (
        "Reports",
        (
            ("reports", "Snapshot freshness"),
        ),
    ),
    (
        "Claude Code Boundary",
        (
            ("hygiene", "Project boundary files"),
        ),
    ),
    (
        "Agent Runtime Guards",
        (
            ("hermes-guard", "Hermes hooks/MCP guard"),
            ("platform-agent-guards", "Agent roles and platform guards"),
            ("deepseek-harness-desktop", "DeepSeek Desktop declaration (not a runtime guard)"),
        ),
    ),
    (
        "Validation",
        (
            ("tests", "Script test suite"),
        ),
    ),
)


def _print_check(checks: dict[str, dict[str, Any]], check_id: str, label: str) -> None:
    check = checks.get(check_id)
    if check is None:
        print(f"  - {label}: SKIPPED - check not configured.")
        return
    print(f"  - {label}: {check['status']} - {check['summary']}")
    if check_id == "reports" and check["status"] in {"FAIL", "ERROR"}:
        print("    Remedy: run `workspace reports status --strict`, then `workspace reports refresh all-current` if the stale reports are expected.")
    if check_id == "tests" and check["status"] == "SKIPPED":
        print("    Note: omitted by default to keep `workspace health` fast; run `workspace health --with-tests` for the full suite.")


def render_text(payload: dict[str, Any]) -> None:
    print(f"Workspace health: {payload['status']}")
    checks = {check["check_id"]: check for check in payload["checks"]}
    if not payload["with_tests"]:
        checks["tests"] = {
            "check_id": "tests",
            "status": "SKIPPED",
            "summary": "full script suite not run.",
        }
    for group_name, items in HEALTH_GROUPS:
        print(f"\n{group_name}")
        for check_id, label in items:
            _print_check(checks, check_id, label)
    if not payload["with_tests"]:
        print("")
        print("Tip: `workspace health` is read-only and lightweight. Use `workspace health --with-tests` before commit-sized changes.")
    print(payload["note"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run live read-only workspace health checks.")
    parser.add_argument("--with-tests", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    payload = run_health(with_tests=args.with_tests)
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        render_text(payload)
    if payload["status"] == "PASS":
        return 0
    if payload["status"] == "NEEDS_ATTENTION":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
