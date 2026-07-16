#!/usr/bin/env python3
"""Verify a generated qq-chat-raw-filter public projection."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from scripts.workspace.runtime import WORKSPACE_ROOT

from scripts.publishing.qq_raw_filter_public_checks import (
    check_forbidden_paths,
    check_required,
    check_text,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a generated qq-chat-raw-filter projection.")
    parser.add_argument("--dir", required=True)
    parser.add_argument("--skip-tests", action="store_true")
    root = Path(parser.parse_args().dir).resolve()
    if not root.is_dir():
        print(f"ERROR: not a directory: {root}", file=sys.stderr)
        return 1

    issues: list[str] = []
    for check in (check_required, check_forbidden_paths, check_text):
        issues.extend(check(root))

    if not parser.parse_args().skip_tests:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests", "-q"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode:
            issues.append(f"Public pytest failed: {(result.stdout + result.stderr).strip()[-500:]}")

    if issues:
        print(f"FAILED: {len(issues)} issue(s) found.")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    print("PASSED: qq-chat-raw-filter projection is ready to publish.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
