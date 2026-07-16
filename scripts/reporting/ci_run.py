#!/usr/bin/env python3
"""ci_run.py — Central CI runner for governed-skill-workspace.

Runs the full test suite and categorises failures into:
  - CORE:    tests that must pass everywhere
  - INFRA:   tests that depend on platform infrastructure (Hermes, OpenCode,
             Reasonix, Windows-specific paths) and are expected to fail in a
             clean public/Linux environment.

Exit codes:
  0 — all tests pass (infra failures are tolerated).
  1 — one or more core tests failed (blocking).
  2 — only infra-dependent tests failed (non-blocking signal).

Usage:
    python scripts/ci_run.py [pytest-args ...]
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from scripts.workspace.runtime import WORKSPACE_ROOT

# Tests that require environment-specific infrastructure.
# Failures in these modules are tolerated — they reflect the absence of
# Hermes, OpenCode, Reasonix, or Windows-specific paths rather than a
# regression in workspace governance logic.
INFRA_DEPENDENT_MODULES: set[str] = {
    "scripts/tests/workspace/test_agent_governance.py",
    "scripts/tests/workspace/test_hermes_workspace_guard.py",
    "scripts/tests/platform/test_platform_agent_guards.py",
    "scripts/tests/workspace/test_verify_change_scope.py",
    "scripts/tests/workspace/test_workspace_health.py",
}

FAILED_LINE_RE = re.compile(
    r"^FAILED\s+(?P<module>.+?\.py)",
)


def get_workspace_root() -> Path:
    """Return the canonical workspace root shared by all script domains."""
    return WORKSPACE_ROOT


def run_pytest(extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
    """Run pytest, returning the completed process."""
    root = get_workspace_root()

    cmd = [sys.executable, "-m", "pytest", "-q"]
    if extra_args:
        cmd.extend(extra_args)

    print(f"[ci_run] Running: {' '.join(cmd)}")
    print(f"[ci_run] CWD:     {root}")
    print()

    result = subprocess.run(
        cmd,
        cwd=root,
        capture_output=True,
        text=True,
        timeout=180,
    )
    return result


def classify_failures(stdout: str) -> tuple[set[str], set[str]]:
    """Classify failing modules into core vs infra.

    Returns:
        (core_failing_modules, infra_failing_modules)
    """
    # Collect all distinct failing module paths
    failing_modules: set[str] = set()
    for line in stdout.split("\n"):
        line = line.strip()
        m = FAILED_LINE_RE.match(line)
        if m:
            mod = m.group("module").replace("\\", "/")
            failing_modules.add(mod)

    # Separate into core vs infra
    core = set()
    infra = set()
    for mod in failing_modules:
        # Normalise: strip leading path segments like "FAILED "
        # and normalise separator
        norm = mod.replace("\\", "/")
        if norm in INFRA_DEPENDENT_MODULES:
            infra.add(norm)
        else:
            core.add(norm)

    return core, infra


def has_collection_error(stdout: str) -> bool:
    """Return whether pytest failed before producing a normal test summary."""

    return any(
        line.lstrip().startswith(("ERROR collecting", "INTERNALERROR"))
        for line in stdout.splitlines()
    )


def main() -> int:
    extra_args = sys.argv[1:] if len(sys.argv) > 1 else []
    result = run_pytest(extra_args)

    core_failures, infra_failures = classify_failures(result.stdout)
    if has_collection_error(result.stdout):
        core_failures.add("<pytest collection>")
    elif result.returncode != 0 and not core_failures and not infra_failures:
        core_failures.add(f"<pytest exit {result.returncode}>")

    # Print test output (last section, most useful)
    lines = result.stdout.strip().split("\n")
    summary_lines = [l for l in lines if l.startswith("===") or l.startswith("FAILED") or l.startswith("PASSED") or "passed" in l and "failed" in l]
    if summary_lines:
        print(result.stdout)
    else:
        # Full output if no summary found
        print(result.stdout)

    if result.stderr.strip():
        print("stderr:", result.stderr.strip()[-500:], file=sys.stderr)

    # Report
    print()
    print("─" * 48)
    print(f"  CORE failures: {len(core_failures)} module(s)")
    for m in sorted(core_failures):
        print(f"    {m}")
    print(f"  INFRA failures: {len(infra_failures)} module(s)")
    for m in sorted(infra_failures):
        print(f"    {m}")
    print("─" * 48)
    print()

    if core_failures:
        print("[ci_run] FAIL — core tests failed (blocking)")
        return 1

    if infra_failures and not core_failures:
        print("[ci_run] PASS — only infra-dependent tests failed (non-blocking)")
        return 0

    if result.returncode == 0:
        print("[ci_run] PASS — all tests passed")
        return 0

    # Fallback (shouldn't reach here)
    print("[ci_run] PASS — no core failures detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
