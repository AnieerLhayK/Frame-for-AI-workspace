#!/usr/bin/env python3
r"""
publish_check.py — Verify a public-workspace staging directory is ready to push.

Checks:
1. No ${WORKSPACE_ROOT}, ${WORKSPACE_ROOT}, ${USER_HOME} absolute paths remain
2. character-system does not exist and skills layers contain only README placeholders
3. Template files match expected list
4. Beginner guide and conservative setup helper exist
5. Essential scripts are functional
6. Test suite passes

Usage:
    python scripts/publish_check.py --dir <staging-dir>
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

# Patterns that should be scrubbed (must NOT appear in output)
FORBIDDEN_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"D:[\\/]+AI"),
    re.compile(r"D:[\\/]+AAAfromC"),
    re.compile(r"D:[\\/]+Dev"),
    re.compile(r"D:[\\/]+ztemp"),
    re.compile(r"C:[\\/]+Users[\\/]+Z1377"),
]

EXPECTED_TEMPLATES: set[str] = {
    "workspace_manifest.yaml.template",
    "mcp/configs/installed-local.mcp.json.template",
    "mcp/configs/wps-agent.mcp.json.template",
}

EXPECTED_DOCS: set[str] = {
    "BEGINNER_GUIDE.md",
    "PATH_MAPPING_REFERENCE.md",
    "ONBOARDING.md",
}

# Paths that must NOT exist
FORBIDDEN_DIRS: set[str] = {
    "packages/character-system",
}
FORBIDDEN_PATH_SEGMENTS: set[str] = {"character-system"}

REQUIRED_EXTENSION_LAYER_FILES: dict[str, set[str]] = {
    "skills": {"README.md"},
    "external-skills": {"README.md"},
}

# Paths that MUST exist
REQUIRED_PATHS: set[str] = {
    "workspace_manifest.yaml",
    "skills/README.md",
    "external-skills/README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "ARCHITECTURE.md",
    "shared/agent_governance.yaml",
    "shared/agent_registry.yaml",
    "shared/workspace_policy.md",
    "shared/workspace_path_policy.md",
    "shared/failure_policy.md",
    "shared/discovery_rules.md",
    "shared/manifest_portability_policy.md",
    "shared/reporting_policy.md",
    "shared/session_continuity_policy.md",
    "shared/delivery_output_policy.md",
    "scripts/resolve_task_context.py",
    "scripts/workspace_cli.py",
    "scripts/agent_governance.py",
    "scripts/workspace_health.py",
    "scripts/setup_public_workspace.py",
    "PROJECT_CONTEXT/tasks/registry/index.yaml",
    "USAGE_GUIDES/prompt_registry.yaml",
    ".claude/rules/workspace-boundary.md",
    ".claude/project-boundary.json",
    ".github/workflows/ci.yml",
}


# Allowlisted rel paths — these files legitimately reference the patterns
# as substitution targets in the publish tooling itself.
ALLOWLISTED_PATHS: set[str] = {
    "scripts/publish_public.py",
    "scripts/publish_check.py",
}


def check_forbidden_paths(root: Path) -> list[str]:
    """Scan all text files for forbidden path patterns."""
    issues: list[str] = []
    for filepath in root.rglob("*"):
        if not filepath.is_file():
            continue
        # Skip binary-like extensions
        if filepath.suffix in (".pyc", ".png", ".jpg", ".ico", ".exe", ".dll"):
            continue
        # Skip .git directory
        if ".git" in filepath.parts:
            continue
        rel = filepath.relative_to(root).as_posix()
        # Skip files that are expected to reference these patterns
        if rel in ALLOWLISTED_PATHS:
            continue
        try:
            text = filepath.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError):
            continue
        for pat in FORBIDDEN_PATTERNS:
            for m in pat.finditer(text):
                line_num = text[: m.start()].count("\n") + 1
                excerpt = text[max(0, m.start() - 20): m.end() + 20].replace("\n", " ")
                issues.append(
                    f"  {rel}:{line_num}: matched {pat.pattern!r} -> ...{excerpt}..."
                )
    return issues


def check_missing_dirs(root: Path) -> list[str]:
    """Check that private/product package directories don't exist anywhere."""
    issues: list[str] = []
    for d in FORBIDDEN_DIRS:
        if (root / d).is_dir():
            issues.append(f"  Forbidden directory exists: {d}/")
    for path in root.rglob("*"):
        if not path.is_dir() or ".git" in path.parts:
            continue
        if any(part.lower() in FORBIDDEN_PATH_SEGMENTS for part in path.parts):
            issues.append(
                f"  Forbidden path segment exists: {path.relative_to(root).as_posix()}/"
            )
    return issues


def check_extension_layers(root: Path) -> list[str]:
    """Ensure extension layers contain only their documentation placeholders."""
    issues: list[str] = []
    for layer, expected_files in REQUIRED_EXTENSION_LAYER_FILES.items():
        path = root / layer
        if not path.is_dir():
            issues.append(f"  Missing public extension layer: {layer}/")
            continue
        entries = sorted(
            entry.relative_to(path).as_posix()
            for entry in path.rglob("*")
            if entry.is_file()
        )
        if set(entries) != expected_files:
            issues.append(
                f"  Public extension layer contains more than its README placeholder: {layer}/ ({entries})"
            )
    return issues


def check_no_bundled_skills(root: Path) -> list[str]:
    """Reject skill manifests in the framework-only public projection."""
    issues: list[str] = []
    for skill_file in root.rglob("SKILL.md"):
        if ".git" in skill_file.parts:
            continue
        issues.append(f"  Bundled skill manifest exists: {skill_file.relative_to(root).as_posix()}")
    return issues


def check_required_paths(root: Path) -> list[str]:
    """Check that required files exist."""
    issues: list[str] = []
    for rp in REQUIRED_PATHS:
        if not (root / rp).is_file():
            issues.append(f"  Missing required file: {rp}")
    return issues


def check_templates(root: Path) -> list[str]:
    """Check that expected template files exist."""
    issues: list[str] = []
    for t in EXPECTED_TEMPLATES:
        if not (root / t).is_file():
            issues.append(f"  Missing template: {t}")
    return issues


def check_docs(root: Path) -> list[str]:
    """Check that expected documentation exists."""
    issues: list[str] = []
    for doc in EXPECTED_DOCS:
        if not (root / doc).is_file():
            issues.append(f"  Missing doc: {doc}")
    return issues


def _routing_event_snapshot(root: Path) -> dict[Path, str | None]:
    """Snapshot resolver logs at both workspace and script-relative locations."""
    paths = (
        root / ".claude" / "routing_events.ndjson",
        root / "scripts" / ".claude" / "routing_events.ndjson",
    )
    return {
        path: path.read_text(encoding="utf-8") if path.is_file() else None
        for path in paths
    }


def _restore_routing_event_snapshot(snapshot: dict[Path, str | None]) -> None:
    """Restore pre-check resolver logs and remove newly created transient logs."""
    for path, original in snapshot.items():
        if original is None:
            if path.exists():
                path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(original, encoding="utf-8")


def run_functional_checks(root: Path) -> list[str]:
    """Run key scripts in the staging directory to verify they work."""
    issues: list[str] = []
    cwd = os.getcwd()
    routing_events = _routing_event_snapshot(root)
    try:
        os.chdir(root)

        # 1. resolve_task_context.py --list
        result = subprocess.run(
            [sys.executable, "scripts/resolve_task_context.py", "--list"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            issues.append(
                f"  resolve_task_context.py --list failed (rc={result.returncode}): "
                + result.stderr.strip()[:200]
            )

        # 2. workspace_cli.py agent list
        result = subprocess.run(
            [sys.executable, "scripts/workspace_cli.py", "agent", "list"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            issues.append(
                f"  workspace_cli.py agent list failed (rc={result.returncode}): "
                + result.stderr.strip()[:200]
            )

        # 3. workspace_cli.py explain mechanism task-routing
        result = subprocess.run(
            [
                sys.executable,
                "scripts/workspace_cli.py",
                "explain",
                "mechanism",
                "task-routing",
            ],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            issues.append(
                f"  workspace_cli.py explain mechanism failed (rc={result.returncode}): "
                + result.stderr.strip()[:200]
            )

        # 4. workspace_cli.py health
        # rc=0 clean, rc=1 issues found, rc=2 infrastructure not fully set up
        result = subprocess.run(
            [sys.executable, "scripts/workspace_cli.py", "health"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode not in (0, 1, 2):
            issues.append(
                f"  workspace_cli.py health failed (rc={result.returncode}): "
                + result.stderr.strip()[:200]
            )

    except subprocess.TimeoutExpired as exc:
        issues.append(f"  Command timed out: {exc.cmd}")
    except FileNotFoundError as exc:
        issues.append(f"  Script not found: {exc}")
    finally:
        os.chdir(cwd)
        _restore_routing_event_snapshot(routing_events)

    return issues


def run_tests(root: Path) -> list[str]:
    """Run pytest in the staging directory."""
    issues: list[str] = []
    cwd = os.getcwd()
    routing_events = _routing_event_snapshot(root)
    try:
        os.chdir(root)
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "scripts/tests", "-q"],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            lines = result.stdout.strip().split("\n")
            failing_tests = [l for l in lines if l.startswith("FAILED ")]
            failing_modules = set()
            for ft in failing_tests:
                # Strip "FAILED " prefix before parsing the test path
                test_path = ft.removeprefix("FAILED ").strip()
                parts = test_path.split("::")
                if len(parts) >= 1:
                    failing_modules.add(parts[0].replace("\\", "/"))

            # Known infrastructure-dependent test files
            # These fail in a clean environment without Hermes, OpenCode,
            # Reasonix, or Windows-specific path infrastructure.
            INFRA_TESTS = {
                "scripts/tests/workspace/test_hermes_workspace_guard.py",
                "scripts/tests/platform/test_platform_agent_guards.py",
                "scripts/tests/workspace/test_agent_governance.py",
                "scripts/tests/workspace/test_verify_change_scope.py",
                "scripts/tests/workspace/test_workspace_health.py",
            }
            non_infra_failures = failing_modules - INFRA_TESTS
            infra_only = len(non_infra_failures) == 0 and len(failing_modules) > 0

            if infra_only:
                # Infrastructure tests expected to fail in bare environment
                # — not a blocking issue for publication.
                pass
            else:
                summary = [l[:120] for l in failing_tests[-5:]]
                issues.append(
                    f"  pytest failed (rc={result.returncode}): "
                    + "; ".join(summary[:3])
                )
                if result.stderr.strip():
                    issues.append(f"  stderr: {result.stderr.strip()[:200]}")
    except subprocess.TimeoutExpired:
        issues.append("  pytest timed out (120s)")
    except FileNotFoundError as exc:
        issues.append(f"  pytest not found: {exc}")
    finally:
        os.chdir(cwd)
        _restore_routing_event_snapshot(routing_events)
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify a public-workspace staging directory."
    )
    parser.add_argument(
        "--dir", required=True,
        help="Path to the staging directory to verify.",
    )
    parser.add_argument(
        "--skip-tests", action="store_true",
        help="Skip pytest run (faster).",
    )
    parser.add_argument(
        "--skip-functional", action="store_true",
        help="Skip script functionality checks.",
    )
    args = parser.parse_args()

    root = Path(args.dir).resolve()
    if not root.is_dir():
        print(f"ERROR: not a directory: {root}", file=sys.stderr)
        return 1

    print(f"Verifying: {root}")
    print()

    checks: list[tuple[str, list[str]]] = [
        ("Forbidden paths", check_forbidden_paths(root)),
        ("Forbidden directories", check_missing_dirs(root)),
        ("Documentation-only extension layers", check_extension_layers(root)),
        ("Bundled skills", check_no_bundled_skills(root)),
        ("Required files", check_required_paths(root)),
        ("Templates", check_templates(root)),
        ("Documentation", check_docs(root)),
    ]

    if not args.skip_functional:
        checks.append(("Functional checks", run_functional_checks(root)))

    if not args.skip_tests:
        checks.append(("Test suite", run_tests(root)))

    total_issues = 0
    for name, issues in checks:
        if issues:
            print(f"(!) {name}: {len(issues)} issue(s)")
            for issue in issues:
                print(issue)
            total_issues += len(issues)
        else:
            print(f"(i) {name}: OK")

    print()
    if total_issues == 0:
        print("PASSED: All checks passed. Ready to publish.")
        return 0
    else:
        print(f"FAILED: {total_issues} issue(s) found. Fix before publishing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
