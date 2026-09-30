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


def module_path(module: str) -> Path:
    if not module.startswith("scripts."):
        raise ValueError(f"Module escapes scripts package: {module}")
    candidate = WORKSPACE_ROOT.joinpath(*module.split(".")).with_suffix(".py").resolve()
    if not candidate.is_relative_to(SCRIPTS_ROOT.resolve()):
        raise ValueError(f"Module escapes scripts root: {module}")
    return candidate


def powershell_executable() -> str:
    return shutil.which("powershell.exe") or shutil.which("pwsh") or "powershell.exe"


def run_python_module(module: str, arguments: Sequence[str]) -> int:
    return subprocess.run(
        [sys.executable, "-m", module, *arguments],
        cwd=WORKSPACE_ROOT,
        check=False,
    ).returncode

def run_powershell_script(name: str, arguments: Sequence[str]) -> int:
    return subprocess.run(
        [powershell_executable(), "-ExecutionPolicy", "Bypass", "-File", str((SCRIPTS_ROOT / name).resolve()), *arguments],
        cwd=WORKSPACE_ROOT,
        check=False,
    ).returncode
