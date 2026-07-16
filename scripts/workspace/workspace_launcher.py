from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


from scripts.workspace.runtime import WORKSPACE_ROOT
CLI_PATH = WORKSPACE_ROOT / "scripts" / "workspace_cli.py"
DEFAULT_INSTALL_DIR = Path.home() / ".local" / "bin"
LAUNCHER_NAME = "workspace.cmd"
MARKER = "workspace-cli-managed-launcher"


def launcher_content(cli_path: Path = CLI_PATH) -> str:
    return "\r\n".join(
        [
            "@echo off",
            f"rem {MARKER}",
            (
                "@setlocal EnableDelayedExpansion"
                ' & set "PYTHONUTF8=1" & set "WORKSPACE_LAUNCHER_PATH=%~f0"'
                f' & python "{cli_path}" %*'
                " & exit /b !errorlevel!"
            ),
            "",
        ]
    )


def path_entries() -> set[str]:
    return {
        os.path.realpath(entry).casefold()
        for entry in os.environ.get("PATH", "").split(os.pathsep)
        if entry.strip()
    }


def inspect_launcher(install_dir: Path) -> dict[str, Any]:
    launcher = install_dir / LAUNCHER_NAME
    exists = launcher.is_file()
    managed = False
    current = False
    if exists:
        text = launcher.read_text(encoding="utf-8", errors="replace")
        managed = MARKER in text
        current = text.replace("\r\n", "\n") == launcher_content().replace("\r\n", "\n")
    return {
        "launcher_path": str(launcher),
        "exists": exists,
        "managed": managed,
        "current": current,
        "directory_on_path": str(install_dir.resolve()).casefold() in path_entries(),
    }


def install_launcher(install_dir: Path, dry_run: bool = False) -> dict[str, Any]:
    status = inspect_launcher(install_dir)
    if status["exists"] and not status["managed"]:
        return {
            "status": "BLOCKED",
            **status,
            "message": "An unmanaged workspace.cmd already exists; it was not replaced.",
        }

    if not dry_run:
        install_dir.mkdir(parents=True, exist_ok=True)
        (install_dir / LAUNCHER_NAME).write_text(
            launcher_content(),
            encoding="utf-8",
            newline="",
        )
    updated = inspect_launcher(install_dir) if not dry_run else status
    return {
        "status": "DRY_RUN" if dry_run else "INSTALLED",
        **updated,
        "message": (
            f"Would install {install_dir / LAUNCHER_NAME}."
            if dry_run
            else "Launcher installed. Open a new terminal if the command is not immediately visible."
        ),
    }


def schedule_delete(path: Path) -> None:
    code = (
        "import os,time;"
        "time.sleep(0.75);"
        f"os.remove({str(path)!r}) if os.path.exists({str(path)!r}) else None"
    )
    creation_flags = 0
    if os.name == "nt":
        creation_flags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
    subprocess.Popen(
        [sys.executable, "-c", code],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        creationflags=creation_flags,
    )


def uninstall_launcher(install_dir: Path, dry_run: bool = False) -> dict[str, Any]:
    status = inspect_launcher(install_dir)
    if not status["exists"]:
        return {"status": "ABSENT", **status, "message": "No launcher is installed."}
    if not status["managed"]:
        return {
            "status": "BLOCKED",
            **status,
            "message": "The existing launcher is not managed by this workspace and was not removed.",
        }
    launcher = install_dir / LAUNCHER_NAME
    active_path = os.environ.get("WORKSPACE_LAUNCHER_PATH")
    active_launcher = (
        os.name == "nt"
        and bool(active_path)
        and os.path.realpath(str(active_path))
        == os.path.realpath(str(launcher))
    )
    if not dry_run and active_launcher:
        schedule_delete(launcher)
        return {
            "status": "UNINSTALL_SCHEDULED",
            **status,
            "message": "Managed launcher removal is scheduled after this command exits.",
        }
    if not dry_run:
        launcher.unlink()
    return {
        "status": "DRY_RUN" if dry_run else "UNINSTALLED",
        **inspect_launcher(install_dir),
        "message": (
            f"Would remove {install_dir / LAUNCHER_NAME}."
            if dry_run
            else "Managed launcher removed."
        ),
    }


def render_text(result: dict[str, Any]) -> None:
    print(f"Launcher: {result['status']}")
    print(f"Path: {result['launcher_path']}")
    print(f"On PATH: {result['directory_on_path']}")
    print(result["message"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the user-local workspace command.")
    parser.add_argument("action", choices=("install", "status", "uninstall"))
    parser.add_argument("--install-dir", type=Path, default=DEFAULT_INSTALL_DIR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    install_dir = args.install_dir.expanduser().resolve()
    if args.action == "install":
        result = install_launcher(install_dir, args.dry_run)
    elif args.action == "uninstall":
        result = uninstall_launcher(install_dir, args.dry_run)
    else:
        status = inspect_launcher(install_dir)
        if status["current"]:
            launcher_status = "INSTALLED"
            message = "The managed launcher is current."
        elif status["managed"]:
            launcher_status = "STALE"
            message = "The managed launcher is stale; run install to refresh it."
        elif status["exists"]:
            launcher_status = "UNMANAGED"
            message = "An unmanaged workspace.cmd exists and will not be modified."
        else:
            launcher_status = "ABSENT"
            message = "Install the launcher to use the short command."
        result = {
            "status": launcher_status,
            **status,
            "message": message,
        }

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        render_text(result)
    return 1 if result["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
