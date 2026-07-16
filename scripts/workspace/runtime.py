"""Shared runtime seams for workspace scripts."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ROOT = WORKSPACE_ROOT / "scripts"


def workspace_root() -> Path:
    return WORKSPACE_ROOT


def scripts_root() -> Path:
    return SCRIPTS_ROOT


def legacy_script_path(name: str) -> Path:
    candidate = (SCRIPTS_ROOT / name).resolve()
    if not candidate.is_relative_to(SCRIPTS_ROOT.resolve()):
        raise ValueError(f"Script path escapes scripts root: {name}")
    return candidate


def powershell_executable() -> str:
    return shutil.which("powershell.exe") or shutil.which("pwsh") or "powershell.exe"


def run_python_script(name: str, arguments: Sequence[str]) -> int:
    return subprocess.run(
        [sys.executable, str(legacy_script_path(name)), *arguments],
        cwd=WORKSPACE_ROOT,
        check=False,
    ).returncode

def run_powershell_script(name: str, arguments: Sequence[str]) -> int:
    return subprocess.run(
        [powershell_executable(), "-ExecutionPolicy", "Bypass", "-File", str(legacy_script_path(name)), *arguments],
        cwd=WORKSPACE_ROOT,
        check=False,
    ).returncode
