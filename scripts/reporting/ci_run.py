#!/usr/bin/env python3
"""ci_run.py — Central CI runner for governed-skill-workspace.

Runs the full test suite and categorises failures into:
  - CORE:    tests that must pass everywhere
  - INFRA:   tests that depend on platform infrastructure (Hermes, OpenCode,
             Windows-specific paths) and are expected to fail in a
             clean public/Linux environment.

Exit codes:
  0 — all tests pass (infra failures are tolerated).
  1 — one or more core tests failed (blocking).
  2 — invalid command-line arguments.

Usage:
    python -m scripts.reporting.ci_run [--suite-timeout SECONDS] [pytest-args ...]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from scripts.workspace.runtime import WORKSPACE_ROOT
from scripts.workspace.manifest_loader import load_manifest

DEFAULT_SUITE_TIMEOUT = 600

# Tests that require environment-specific infrastructure.
# Failures in these modules are tolerated — they reflect the absence of
# Hermes, OpenCode, or Windows-specific paths rather than a
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


@dataclass(frozen=True)
class TestSuite:
    """A pytest suite with the import root required by its tests."""

    name: str
    cwd: Path
    test_path: Path


@dataclass(frozen=True)
class SuiteResult:
    """Pytest output plus bounded execution evidence, including timeout output."""

    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool
    timeout_seconds: int


def build_test_suites(root: Path | None = None) -> tuple[TestSuite, ...]:
    """Return governed suites with isolated working directories.

    Some standalone packages intentionally use local imports (for example,
    ``qq_raw_filter`` and the disk-scan ``scripts`` package). Running all
    tests from the workspace root makes the root ``scripts`` package shadow
    those local packages. Each suite therefore runs from its own package
    root, while the workspace suite keeps the historical root import surface.
    """
    workspace_root = root or get_workspace_root()
    qq_root = (
        workspace_root
        / "packages"
        / "character-system"
        / "engineering"
        / "corpus-preparation"
        / "qq-raw-material-filter"
    )
    manifest = load_manifest(workspace_root / "workspace_manifest.yaml")
    disk_scan = next(
        (skill for skill in manifest.get("skills", []) if skill.get("id") == "disk-scan-reporter"),
        None,
    )
    candidates = [
        TestSuite("workspace", workspace_root, Path("scripts/tests")),
        TestSuite("qq-raw-material-filter", qq_root, Path("tests")),
    ]
    if disk_scan is not None:
        source = disk_scan.get("source_path")
        if not isinstance(source, str) or not source:
            raise ValueError("Registered disk-scan-reporter has no source_path")
        disk_scan_root = (workspace_root / source).resolve()
        if not disk_scan_root.is_relative_to(workspace_root.resolve()):
            raise ValueError("Registered disk-scan-reporter source escapes the workspace")
        if not (disk_scan_root / "tests").is_dir():
            raise ValueError("Registered disk-scan-reporter tests are missing")
        candidates.append(TestSuite("disk-scan-reporter", disk_scan_root, Path("tests")))
    return tuple(
        suite
        for suite in candidates
        if suite.name == "workspace" or (suite.cwd / suite.test_path).is_dir()
    )


def get_workspace_root() -> Path:
    """Return the canonical workspace root shared by all script domains."""
    return WORKSPACE_ROOT


def run_test_suites(
    extra_args: list[str] | None = None,
    *,
    verbose: bool = True,
    suite_timeout: int = DEFAULT_SUITE_TIMEOUT,
) -> list[tuple[TestSuite, SuiteResult]]:
    """Run all pytest suites from their package-local import roots."""
    if suite_timeout <= 0:
        raise ValueError("suite_timeout must be positive")
    results: list[tuple[TestSuite, SuiteResult]] = []
    for suite in build_test_suites():
        cmd = [sys.executable, "-m", "pytest", "-q", str(suite.test_path)]
        if extra_args:
            cmd.extend(extra_args)
        if verbose:
            print(f"[ci_run] Suite:   {suite.name}")
            print(f"[ci_run] Running: {' '.join(cmd)}")
            print(f"[ci_run] CWD:     {suite.cwd}")
            print()
        started = time.monotonic()
        try:
            process = subprocess.run(
                cmd,
                cwd=suite.cwd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=suite_timeout,
            )
            result = SuiteResult(
                process.returncode, process.stdout, process.stderr,
                round(time.monotonic() - started, 3), False, suite_timeout,
            )
        except subprocess.TimeoutExpired as exc:
            def decode(value: str | bytes | None) -> str:
                return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else (value or "")

            result = SuiteResult(
                1, decode(exc.stdout), decode(exc.stderr),
                round(time.monotonic() - started, 3), True, suite_timeout,
            )
        except OSError as exc:
            result = SuiteResult(
                1, "", str(exc), round(time.monotonic() - started, 3),
                False, suite_timeout,
            )
        results.append((suite, result))
    return results


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


def summarize_results(
    suite_results: list[tuple[TestSuite, SuiteResult | subprocess.CompletedProcess[str]]],
) -> dict[str, object]:
    """Return the stable, machine-readable CI classification."""
    core_failures: set[str] = set()
    infra_failures: set[str] = set()
    suites: list[dict[str, object]] = []

    for suite, result in suite_results:
        suite_core, suite_infra = classify_failures(result.stdout)
        core_failures.update(
            f"{suite.name}: {module}" for module in suite_core
        )
        infra_failures.update(
            f"{suite.name}: {module}" for module in suite_infra
        )
        if getattr(result, "timed_out", False):
            core_failures.add(f"{suite.name}: <suite timeout after {result.timeout_seconds}s>")
        elif has_collection_error(result.stdout):
            core_failures.add(f"{suite.name}: <pytest collection>")
        elif result.returncode != 0 and not suite_core and not suite_infra:
            core_failures.add(f"{suite.name}: <pytest exit {result.returncode}>")
        suite_payload = {
            "name": suite.name,
            "returncode": result.returncode,
            "duration_seconds": getattr(result, "duration_seconds", 0.0),
            "timed_out": getattr(result, "timed_out", False),
        }
        if result.returncode != 0:
            suite_payload["stdout"] = result.stdout
            suite_payload["stderr"] = result.stderr
        suites.append(suite_payload)

    return {
        "status": "FAIL" if core_failures else "PASS",
        "core_failures": sorted(core_failures),
        "infra_failures": sorted(infra_failures),
        "suites": suites,
    }


def render_text(
    payload: dict[str, object],
    suite_results: list[tuple[TestSuite, SuiteResult | subprocess.CompletedProcess[str]]],
) -> None:
    """Render the legacy human-oriented output without changing exit semantics."""
    for suite, result in suite_results:
        print(result.stdout)
        if result.stderr.strip():
            print(
                f"stderr ({suite.name}): {result.stderr.strip()[-500:]}",
                file=sys.stderr,
            )

    print()
    print("─" * 48)
    core_failures = list(payload["core_failures"])
    infra_failures = list(payload["infra_failures"])
    print(f"  CORE failures: {len(core_failures)} module(s)")
    for m in core_failures:
        print(f"    {m}")
    print(f"  INFRA failures: {len(infra_failures)} module(s)")
    for m in infra_failures:
        print(f"    {m}")
    print("─" * 48)
    print()

    if payload["status"] == "FAIL":
        print("[ci_run] FAIL — core tests failed (blocking)")
    elif infra_failures:
        print("[ci_run] PASS — only infra-dependent tests failed (non-blocking)")
    else:
        print("[ci_run] PASS — all tests passed")


def main(argv: list[str] | None = None) -> int:
    def positive_seconds(value: str) -> int:
        try:
            seconds = int(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("suite timeout must be a positive integer") from exc
        if seconds <= 0:
            raise argparse.ArgumentTypeError("suite timeout must be a positive integer")
        return seconds

    parser = argparse.ArgumentParser(description="Run governed CI test suites.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--suite-timeout", type=positive_seconds, default=DEFAULT_SUITE_TIMEOUT)
    args, extra_args = parser.parse_known_args(argv)
    try:
        suite_results = run_test_suites(
            extra_args, verbose=args.format == "text", suite_timeout=args.suite_timeout,
        )
    except (ValueError, OSError) as exc:
        payload = {"status": "FAIL", "core_failures": ["<suite discovery>"], "infra_failures": [], "suites": [], "errors": [str(exc)]}
        if args.format == "json":
            print(json.dumps(payload, sort_keys=True))
        else:
            print(f"[ci_run] FAIL — {exc}", file=sys.stderr)
        return 1
    payload = summarize_results(suite_results)
    if args.format == "json":
        print(json.dumps(payload, sort_keys=True))
    else:
        render_text(payload, suite_results)
    return 1 if payload["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
