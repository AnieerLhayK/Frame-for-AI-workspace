#!/usr/bin/env python3
"""Conservative first-run setup for the public workspace skeleton.

This helper makes the repository minimally runnable. It copies template files,
replaces only standard path variables, and runs read-only self-checks. It does
not configure provider credentials, install platform plugins, write outside the
repository except the selected data root, or create AI-platform projections.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


TEMPLATE_FILES = (
    "workspace_manifest.yaml",
    "mcp/configs/installed-local.mcp.json",
    "mcp/configs/wps-agent.mcp.json",
)


def run(command: list[str], root: Path, *, required: bool) -> bool:
    print("+ " + " ".join(command))
    result = subprocess.run(command, cwd=root, check=False)
    if result.returncode == 0:
        return True
    label = "required" if required else "optional"
    print(f"[{label} check failed] exit code {result.returncode}: {' '.join(command)}")
    return not required


def render_template(path: Path, replacements: dict[str, str], *, overwrite: bool) -> str:
    template = path.with_name(path.name + ".template")
    if not template.is_file():
        return "missing-template"
    if path.exists() and not overwrite:
        current = path.read_text(encoding="utf-8")
        if not any(key in current for key in replacements):
            return "kept-existing"
        text = current
        status = "updated-placeholders"
    else:
        text = template.read_text(encoding="utf-8")
        status = "written"

    for key, value in replacements.items():
        text = text.replace(key, value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare the public workspace skeleton for first use.")
    parser.add_argument("--workspace-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--data-root", default=str(Path.home() / ".ai-workspace-data"))
    parser.add_argument("--user-home", default=str(Path.home()))
    parser.add_argument("--dev-root", default=str(Path.home() / "dev"))
    parser.add_argument("--scratch-root", default=str(Path.home() / "tmp"))
    parser.add_argument("--other-project-root", default=str(Path.home() / "projects"))
    parser.add_argument("--overwrite", action="store_true", help="Rewrite generated config files from templates.")
    parser.add_argument("--install-deps", action="store_true", help="Install Python helper dependencies.")
    parser.add_argument("--skip-checks", action="store_true", help="Only write config files; do not run self-checks.")
    args = parser.parse_args()

    root = Path(args.workspace_root).resolve()
    if not (root / "scripts" / "workspace_cli.py").is_file():
        print(f"[FAIL] Not a workspace skeleton root: {root}")
        return 1

    replacements = {
        "${WORKSPACE_ROOT}": root.as_posix(),
        "${DATA_ROOT}": Path(args.data_root).resolve().as_posix(),
        "${USER_HOME}": Path(args.user_home).resolve().as_posix(),
        "${DEV_ROOT}": Path(args.dev_root).resolve().as_posix(),
        "${SCRATCH_ROOT}": Path(args.scratch_root).resolve().as_posix(),
        "${OTHER_PROJECT_ROOT}": Path(args.other_project_root).resolve().as_posix(),
    }

    print("Public workspace first-run setup")
    print(f"Workspace root: {root}")
    print(f"Data root:      {replacements['${DATA_ROOT}']}")
    print("")

    for relative in TEMPLATE_FILES:
        status = render_template(root / relative, replacements, overwrite=args.overwrite)
        print(f"{relative}: {status}")

    data_root = Path(args.data_root).resolve()
    data_root.mkdir(parents=True, exist_ok=True)
    print(f"Ensured data root: {data_root}")

    if args.install_deps:
        requirement_args: list[str] = []
        for relative in ("scripts/requirements-context-tools.txt", "scripts/requirements-publish.txt"):
            path = root / relative
            if path.is_file():
                requirement_args.extend(["-r", str(path)])
        if requirement_args and not run([sys.executable, "-m", "pip", "install", *requirement_args], root, required=True):
            return 1
        if not requirement_args:
            print("[WARN] No requirements files found; skipped dependency install.")

    if args.skip_checks:
        print("")
        print("Skipped self-checks. Next: run `python scripts/workspace_cli.py health`.")
        return 0

    checks = [
        ([sys.executable, "scripts/workspace_cli.py", "--help"], True),
        ([sys.executable, "scripts/workspace_cli.py", "task", "list"], True),
        ([sys.executable, "scripts/workspace_cli.py", "explain", "mechanism", "task-routing"], True),
        ([sys.executable, "scripts/workspace_cli.py", "agent", "list"], False),
        ([sys.executable, "scripts/workspace_cli.py", "health"], False),
    ]

    print("")
    print("Read-only self-checks")
    ok = True
    for command, required in checks:
        ok = run(command, root, required=required) and ok

    print("")
    if ok:
        print("Setup complete. The core CLI, task routing, and explain entrypoint are available.")
    else:
        print("Setup completed with non-blocking environment warnings. Review the output above.")
    print("Provider credentials, plugins, model settings, and platform projections remain explicit manual steps.")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
