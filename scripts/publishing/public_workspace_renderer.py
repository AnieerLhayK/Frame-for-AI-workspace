"""Render public manifest, documents and setup assets from canonical sources."""
from __future__ import annotations
import json
from pathlib import Path
from scripts.workspace.runtime import WORKSPACE_ROOT
from scripts.publishing.readme_templates import load_template, render_template
from scripts.publishing.publish_policy import scrub_content

EXTENSION_LAYER_READMES: dict[str, str] = {
    "skills": load_template("frame/skills.md"),
    "external-skills": load_template("frame/external-skills.md"),
    "packages": load_template("frame/packages.md"),
}

SKELETON_STUB: dict[str, str] = {
    "README.md": load_template("frame/category-readme.md"),
    "SKILL.md": """---
id: {dir_name}
description: Template skill scaffold (replace with actual skill)
role: production
authority:
  default: read
  allowed:
    - invoke
    - record_write
execution_modes:
  default: text_only
  allowed:
    - text_only
    - record_write
platform: claude
---

# {dir_name}

This is a structural placeholder. Implement your skill following the
patterns defined in workspace_manifest.yaml and shared/governance/agent_governance.yaml.

## Registration

To register this skill, add it to its category registry (or package catalog)
with the appropriate role, authority, execution_modes, and exposures. The root
manifest points to catalogs; runtime consumers use the central loader.
""",
    "SHARED_PROTOCOLS.md": """# Shared Protocols

This skill scaffold references domain protocols defined in
packages/character-system/shared/. See that directory for the full set of
protocols available to character-system skills.
""",
}

def generate_public_manifest(source_manifest: Path) -> str:
    """Build a generic manifest without private packages, skills, or links."""
    from scripts.workspace.manifest_loader import load_manifest

    data = load_manifest(source_manifest)
    workspace = data.setdefault("workspace", {})
    workspace["workspace_name"] = "governed-ai-workspace-template"
    workspace["source_of_truth"] = "${WORKSPACE_ROOT}"
    workspace["description"] = (
        "Portable manifest for a governed AI workspace framework."
    )
    data["platform_roots"] = {
        "codex": "${DATA_ROOT}/codex/skills",
        "claude": "${WORKSPACE_ROOT}/.claude/skills",
        "opencode": "${USER_HOME}/.config/opencode/skills",
        "hermes": "${DATA_ROOT}/hermes/skills",
    }
    data["session_stores"] = {
        "claude": {
            "data_root": "${DATA_ROOT}/claude",
            "projects_path": "projects",
            "project_identity": "workspace-root",
        },
        "opencode": {
            "data_root": "${DATA_ROOT}/opencode/current-share",
            "database_path": "opencode.db",
            "project_identity": "git-worktree",
        },
    }
    data["output_roots"] = {"workspace": "${DATA_ROOT}/out/workspace"}
    data["runtime_roots"] = {"staging": "${DATA_ROOT}/codex/cache/staging"}
    data["external_roots"] = {
        "research": "${DATA_ROOT}/research",
        "raw_skills": "${DATA_ROOT}/research/skills",
        "adapted_skills": "${WORKSPACE_ROOT}/external-skills",
    }
    data["packages"] = []
    data["skills"] = []
    data.pop("skill_catalogs", None)
    data["projections"] = []
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"

def generate_public_readme(repo_name: str) -> str:
    """Return the public Frame README with its framework-only boundary explicit."""
    return render_template("frame/README.md", repo_name=repo_name)

def generate_public_readme_zh(repo_name: str) -> str:
    """Return the paired generic Chinese README for the public template."""
    return render_template("frame/README.zh-CN.md", repo_name=repo_name)

def generate_public_architecture_md() -> str:
    """Return a framework-only architecture description."""
    return """# Architecture

This repository is a framework template for a governed AI workspace. It is
organized around a small set of portable layers:

- `workspace_manifest.yaml`: source-of-truth registry for this template.
- `shared/`: reusable policies and contracts for bounded discovery and writes.
- `scripts/`: framework utilities for routing, health, setup, and validation.
- `skills/`: skills developed for your workspace.
- `external-skills/`: reviewed third-party skills.
- `PROJECT_CONTEXT/`: optional workspace memory and routing context.

Add domain packages after reviewing their source,
privacy, licensing, and deployment boundaries.

## Deployment Boundary

The first-run helper configures only template paths and performs read-only
checks. It does not install providers, create platform links, or grant extra
permissions. A healthy deployment means the framework CLI and tests run; a
platform-specific health warning is expected until that platform is configured.
"""

def generate_public_agent_guidance(filename: str) -> str:
    """Return generic agent guidance without private workspace instructions."""
    return f"""# {filename}

This public repository is a governed AI workspace framework template.

## Boundary

- Treat this repository as source for framework structure and policies only.
- Keep credentials, private corpora, personal data, and provider state outside
  the repository.
- Use `skills/` for local skills and `external-skills/` for reviewed imports.
- Add downstream domain packages only after reviewing provenance, privacy,
  licensing, and deployment boundaries.

## Safe Start

Run `python scripts/setup_public_workspace.py`, then use the read-only health,
task-routing, and test commands documented in `BEGINNER_GUIDE.md`.

"""

PUBLIC_QUICK_START_ROOT = WORKSPACE_ROOT / "USAGE_GUIDES" / "QUICK_START"

PUBLIC_TEMPLATE_REPO_NAME = "governed-skill-workspace-template"

def _read_public_guide_source(filename: str) -> str:
    """Read a canonical public guide template from the usage-guide source tree."""
    return (PUBLIC_QUICK_START_ROOT / filename).read_text(encoding="utf-8")

def generate_path_mapping_md() -> str:
    """Return the source guide rendered as root-level PATH_MAPPING_REFERENCE.md."""
    return _read_public_guide_source("path_mapping_reference.md")

def generate_public_setup_py() -> str:
    """Return the conservative setup helper for the public skeleton."""
    return r'''#!/usr/bin/env python3
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
    parser.add_argument("--workspace-root", default=str(WORKSPACE_ROOT))
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
    if not (root / "scripts" / "workspace" / "workspace_cli.py").is_file():
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
        print("Skipped self-checks. Next: run `python -m scripts.workspace.workspace_cli health`.")
        return 0

    checks = [
        ([sys.executable, "-m", "scripts.workspace.workspace_cli", "--help"], True),
        ([sys.executable, "-m", "scripts.workspace.workspace_cli", "task", "list"], True),
        ([sys.executable, "-m", "scripts.workspace.workspace_cli", "explain", "mechanism", "task-routing"], True),
        ([sys.executable, "-m", "scripts.workspace.workspace_cli", "agent", "list"], False),
        ([sys.executable, "-m", "scripts.workspace.workspace_cli", "health"], False),
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
'''

def generate_beginner_guide_md(repo_name: str) -> str:
    """Render the canonical beginner guide for the public repository name."""
    return _read_public_guide_source("beginner_guide.md").replace(
        PUBLIC_TEMPLATE_REPO_NAME, repo_name
    )

def generate_onboarding_md(repo_name: str) -> str:
    """Render the canonical onboarding guide for the public repository name."""
    return _read_public_guide_source("onboarding.md").replace(
        PUBLIC_TEMPLATE_REPO_NAME, repo_name
    )
