#!/usr/bin/env python3
"""
publish_public.py — Generate a scrubbed public-workspace skeleton.

Copies the workspace architecture, strips business code, replaces absolute
paths with template variables, and produces a git-ready public repository.

Usage:
    python scripts/publish_public.py --out-dir <path> [--repo-name <name>]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# ── Path-substitution rules (ordered: longest literal match first) ──────────
SUBSTITUTIONS: list[tuple[re.Pattern[str], str]] = [
    # Windows backslash paths
    (re.escape(r"D:\AAAfromC\source\repos\CNN"),
     "${OTHER_PROJECT_ROOT}/source/repos/CNN"),
    (re.escape(r"D:\AI\data\workspace-governance"),
     "${DATA_ROOT}/workspace-governance"),
    (re.escape(r"D:\AI\data\hermes"),
     "${DATA_ROOT}/hermes"),
    (re.escape(r"D:\AI\data\codex"),
     "${DATA_ROOT}/codex"),
    (re.escape(r"D:\AI\data\claude"),
     "${DATA_ROOT}/claude"),
    (re.escape(r"D:\AI\data\opencode"),
     "${DATA_ROOT}/opencode"),
    (re.escape(r"D:\AI\data\reasonix"),
     "${DATA_ROOT}/reasonix"),
    (re.escape(r"D:\AI\out\workspace"),
     "${DATA_ROOT}/out/workspace"),
    (re.escape(r"D:\AI\out"),
     "${DATA_ROOT}/out"),
    (re.escape(r"D:\AI\data\playwright-mcp"),
     "${DATA_ROOT}/playwright-mcp"),
    (re.escape(r"D:\AI\data\playwright-browsers"),
     "${DATA_ROOT}/playwright-browsers"),
    (re.escape(r"D:\AI\data"),
     "${DATA_ROOT}"),
    (re.escape(r"D:\AI\workspace"),
     "${WORKSPACE_ROOT}"),
    (re.escape(r"D:\AI"),
     "${WORKSPACE_ROOT}"),
    (re.escape(r"D:\Dev"),
     "${DEV_ROOT}"),
    (re.escape(r"D:\ztemp"),
     "${SCRATCH_ROOT}"),
    # Forward-slash variants
    (re.escape(r"D:/AI/data/workspace-governance"),
     "${DATA_ROOT}/workspace-governance"),
    (re.escape(r"D:/AI/data/hermes"),
     "${DATA_ROOT}/hermes"),
    (re.escape(r"D:/AI/data/codex"),
     "${DATA_ROOT}/codex"),
    (re.escape(r"D:/AI/data/claude"),
     "${DATA_ROOT}/claude"),
    (re.escape(r"D:/AI/data/opencode"),
     "${DATA_ROOT}/opencode"),
    (re.escape(r"D:/AI/data/reasonix"),
     "${DATA_ROOT}/reasonix"),
    (re.escape(r"D:/AI/data/"),
     "${DATA_ROOT}/"),
    (re.escape(r"D:/AI/workspace"),
     "${WORKSPACE_ROOT}"),
    (re.escape(r"D:/AI/"),
     "${WORKSPACE_ROOT}/"),
    (re.escape(r"D:/AI"),
     "${WORKSPACE_ROOT}"),
    (re.escape(r"D:/Dev"),
     "${DEV_ROOT}"),
    (re.escape(r"D:/ztemp"),
     "${SCRATCH_ROOT}"),
    # User home paths
    (re.escape(r"C:\Users\Z1377\.config\opencode\skills"),
     "${USER_HOME}/.config/opencode/skills"),
    (re.escape(r"C:\Users\Z1377\.config\opencode"),
     "${USER_HOME}/.config/opencode"),
    (re.escape(r"C:\Users\Z1377\.local\share\opencode"),
     "${USER_HOME}/.local/share/opencode"),
    (re.escape(r"C:\Users\Z1377\.claude"),
     "${USER_HOME}/.claude"),
    (re.escape(r"C:\Users\Z1377\.codex"),
     "${USER_HOME}/.codex"),
    (re.escape(r"C:\Users\Z1377\.cursor"),
     "${USER_HOME}/.cursor"),
    (re.escape(r"C:\Users\Z1377\AppData\Roaming\Cursor"),
     "${USER_HOME}/AppData/Roaming/Cursor"),
    (re.escape(r"C:\Users\Z1377"),
     "${USER_HOME}"),
]

# ── Excluded paths (glob-like, relative to workspace root) ──────────────────
EXCLUDED_PATHS = {
    # Entire directories
    "skills",
    ".agents",
    ".codex",
    ".opencode",
    ".obsidian",
    "external-skills",
    "mcp/servers",
    "mcp/downloads",
    "mcp/logs",
    "publish-staging",
    "corpus",
    "backups",
    "archives",
    "archive",
    # Subdirectory exclusions (full relative path)
    ".claude/skills",
    "reports/legacy_git_metadata",
    "packages/character-system/distribution",
    "WORKSPACE_ENGINEERING/plans/public-repo-plan.md",
    # Individual files
    ".env",
    ".claude/routing_events.ndjson",
    ".claude/settings.local.json",
}

# ── Files that need path scrubbing ──────────────────────────────────────────
SCRUB_FILES: set[str] = {
    "workspace_manifest.yaml",
    "AGENTS.md",
    "shared/agent_registry.yaml",
    "shared/agent_governance.yaml",
    "shared/templates/agent_registration.example.yaml",
    "shared/templates/agent_capability_lease.example.yaml",
    "PROJECT_CONTEXT/task_registry.yaml",
    "PROJECT_CONTEXT/session_migrations.json",
    "PROJECT_CONTEXT/task_ledger.md",
    "PROJECT_CONTEXT/current_status.md",
    "PROJECT_CONTEXT/context_budget.md",
    "WORKSPACE_ENGINEERING/external_knowledge/external_rag_planning.md",
    "USAGE_GUIDES/QUICK_START/claude_code.md",
    "USAGE_GUIDES/QUICK_START/agent_governance.md",
    "scripts/start_hermes_gateway.ps1",
    "scripts/stop_hermes_gateway.ps1",
    "scripts/claude_long_task_notifications/hermes-mcp-client.js",
    "scripts/hermes_workspace_guard.py",
    "scripts/workspace_health.py",
    "scripts/tests/test_workspace_cli.py",
    "scripts/tests/test_hermes_workspace_guard.py",
    "scripts/tests/test_workspace_health.py",
    "scripts/tests/test_agent_governance.py",
    ".claude/rules/workspace-boundary.md",
    "reasonix.toml",
    "mcp/README.md",
    "scripts/sync_public_repo.py",
    "WORKSPACE_ENGINEERING/PUBLISH.md",
}

# ── Files that become .template (also scrubbed) ──────────────────────────────
TEMPLATE_FILES: set[str] = {
    "workspace_manifest.yaml",
    "mcp/configs/installed-local.mcp.json",
    "mcp/configs/wps-agent.mcp.json",
}

# ── Skeleton directories (keep tree, clear business content) ─────────────────
# Each entry: (rel_path, [stub_files], purpose_description)
SKELETON_DIRS: list[tuple[str, list[str], str]] = [
    (
        "packages/character-system/engineering/diagnosis/style-doctor",
        ["SKILL.md", "README.md", "SHARED_PROTOCOLS.md"],
        "Style-doctor skill scaffold — implements feedback-diagnosis role.\n"
        "See shared/agent_governance.yaml → surface_classes for path conventions.",
    ),
    (
        "packages/character-system/engineering/generation/character-generator",
        ["SKILL.md", "README.md", "SHARED_PROTOCOLS.md"],
        "Character-generator skill scaffold — implements production role.\n"
        "Generates characters via configured platform APIs.",
    ),
    (
        "packages/character-system/engineering/maintenance/character-maintainer",
        ["SKILL.md", "README.md", "SHARED_PROTOCOLS.md"],
        "Character-maintainer skill scaffold — implements maintenance role.\n"
        "Handles drift detection, patch application, and version upgrades.",
    ),
    (
        "packages/character-system/runtime/characters/zyc",
        ["SKILL.md", "README.md", "SHARED_PROTOCOLS.md"],
        "Runtime character skill scaffold — implements runtime_character role.\n"
        "Active inference loop with experience accumulation.",
    ),
    (
        "packages/character-system/reports/runtime-loop",
        [],
        "Runtime-loop records: diagnoses, handoffs, drift snapshots.\n"
        "Cleared for public release — add your own records after setup.",
    ),
]

# Stub content for skeleton skill files
SKELETON_STUB: dict[str, str] = {
    "README.md": """# {dir_name}

This is a structural skeleton. See the workspace architecture documentation
for how to implement a skill in this category.

Related:
- workspace_manifest.yaml → skills[] for registration
- shared/agent_governance.yaml → surface class conventions
- ARCHITECTURE.md → layer hierarchy
""",
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
patterns defined in workspace_manifest.yaml and shared/agent_governance.yaml.

## Registration

To register this skill, add an entry in workspace_manifest.yaml → skills[]
with the appropriate role, authority, execution_modes, and exposures.
""",
    "SHARED_PROTOCOLS.md": """# Shared Protocols

This skill scaffold references domain protocols defined in
packages/character-system/shared/. See that directory for the full set of
protocols available to character-system skills.
""",
}

# ── Files that always get copied verbatim ────────────────────────────────────
# (Everything under workspace root not excluded, not a skeleton dir, not explicitly listed)


def _compile_substitutions() -> list[tuple[re.Pattern[str], str]]:
    """Compile substitutions for literal and JSON-escaped Windows paths."""
    compiled: list[tuple[re.Pattern[str], str]] = []
    seen: set[tuple[str, str]] = set()
    for pattern_str, repl in SUBSTITUTIONS:
        variants = [pattern_str]
        flexible_slashes = pattern_str.replace(r"\\", r"[\\/]+")
        if flexible_slashes != pattern_str:
            variants.append(flexible_slashes)
        for variant in variants:
            key = (variant, repl)
            if key in seen:
                continue
            compiled.append((re.compile(variant), repl))
            seen.add(key)
    return compiled


def scrub_content(text: str) -> str:
    """Replace all known absolute-path patterns with template variables."""
    for pattern, repl in _compile_substitutions():
        text = pattern.sub(repl, text)
    return text


def should_exclude(rel_path: str) -> bool:
    """Return True if the relative path should be excluded."""
    parts = rel_path.replace("\\", "/").split("/")
    # Check each prefix of the path against EXCLUDED_PATHS
    cumulative = ""
    for part in parts:
        cumulative = (cumulative + "/" + part) if cumulative else part
        if cumulative in EXCLUDED_PATHS:
            return True
    # Check exact file match
    if rel_path.replace("\\", "/") in EXCLUDED_PATHS:
        return True
    # Exclude __pycache__, .pyc, .DS_Store, Thumbs.db
    name = parts[-1] if parts else ""
    if name in ("__pycache__", ".DS_Store", "Thumbs.db"):
        return True
    if name.endswith(".pyc"):
        return True
    if name.endswith(".vbs"):
        return True
    return False


def is_skeleton_dir(rel_path: str) -> str | None:
    """If rel_path falls under a skeleton dir, return the purpose text."""
    norm = rel_path.replace("\\", "/").rstrip("/")
    for sdir, _stub_files, purpose in SKELETON_DIRS:
        if norm == sdir or norm.startswith(sdir + "/"):
            return purpose
    return None


def needs_scrub(rel_path: str) -> bool:
    """Check if a file needs path scrubbing."""
    norm = rel_path.replace("\\", "/")
    # Check exact match
    if norm in SCRUB_FILES:
        return True
    # Check wildcard patterns
    if norm.startswith("reports/"):
        return True
    if "/reports/" in norm:
        return True
    # All mcp/configs/*.json need scrubbing
    if norm.startswith("mcp/configs/") and norm.endswith(".json"):
        return True
    return False


def is_template(rel_path: str) -> bool:
    """Check if a file should also produce a .template variant."""
    return rel_path.replace("\\", "/") in TEMPLATE_FILES


def generate_path_mapping_md() -> str:
    """Return the content for PATH_MAPPING_REFERENCE.md."""
    return """# PATH_MAPPING_REFERENCE

This workspace skeleton uses template variables to replace machine-specific
absolute paths. Before first use, copy each `.template` file over the real
file and replace the variables with your local paths.

## Template Variables

| Variable | Default (example) | Description |
|----------|-------------------|-------------|
| `${WORKSPACE_ROOT}` | `~/workspace` | Root of the cloned workspace repository |
| `${DATA_ROOT}` | `~/.ai-data` | Base directory for AI-tool runtime data |
| `${USER_HOME}` | `~` (Unix) / `%USERPROFILE%` (Windows) | User home directory |
| `${DEV_ROOT}` | `~/dev` | Development projects root |
| `${SCRATCH_ROOT}` | `~/tmp` | Scratch / temporary directory |
| `${OTHER_PROJECT_ROOT}` | `~/projects` | Other repository roots (multi-project setups) |

## What Needs Configuration

1. **`workspace_manifest.yaml`** — Set `source_of_truth` to your clone path.
   Review `platform_roots.*` and `projections[].link_path` for each AI platform
   you use (Claude Code, Codex, OpenCode, Hermes).

2. **`mcp/configs/installed-local.mcp.json`** — Fix the `python.exe` and
   `node` binary paths, and the filesystem server's allowed directories.

3. **`mcp/configs/wps-agent.mcp.json`** — Fix the `python.exe` path for the
   WPS Office automation server.

4. **`shared/agent_registry.yaml`** — Set `data_root` and `cache_root` for
   each registered agent to match your local environment.

## Verification

After configuration, run:
```bash
python scripts/workspace_cli.py health --with-tests
python scripts/resolve_task_context.py --list
python scripts/workspace_cli.py agent list
```
"""


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
'''


def generate_beginner_guide_md(repo_name: str) -> str:
    """Return beginner-focused guidance for the public skeleton."""
    return f"""# BEGINNER_GUIDE - {repo_name}

This repository is a public skeleton for building a governed AI workspace. It
keeps the workspace's own structure visible: task routing, knowledge lookup,
agent boundaries, report checks, and explainable CLI entrypoints.

## Quick Start

Clone your fork, then run the conservative first-run helper:

```bash
git clone <your-fork-url>
cd {repo_name}
python scripts/setup_public_workspace.py
```

The helper:

- copies `.template` configuration files to their real names when missing;
- replaces standard path variables such as `${{WORKSPACE_ROOT}}` and `${{DATA_ROOT}}`;
- creates the basic data root;
- runs read-only checks for `workspace_cli.py`, task routing, `workspace explain`,
  agent listing, and health.

It does not configure provider credentials, install AI-platform plugins, create
platform projections, or grant extra permissions. Use `--overwrite` only when
you want to regenerate local config files from templates.

## Core Commands To Learn First

```bash
python scripts/workspace_cli.py --help
python scripts/workspace_cli.py task list
python scripts/workspace_cli.py task resolve workspace_developer_experience
python scripts/workspace_cli.py explain mechanism task-routing
python scripts/workspace_cli.py explain path scripts/workspace_cli.py
python scripts/workspace_cli.py agent list
python scripts/workspace_cli.py health
```

These commands show the environment's own basic functions before you add your
own skills or platform integrations.

## What To Configure Manually

After the helper runs, review:

- `workspace_manifest.yaml` for your local source root and platform roots;
- `shared/agent_registry.yaml` for per-agent data/cache roots;
- `mcp/configs/*.json` only if you use those MCP servers;
- platform-specific loading surfaces only after you understand the projection
  model in `ARCHITECTURE.md`.

Keep credentials and provider settings out of this repository unless you have a
separate, private policy for them.
"""


def generate_onboarding_md(repo_name: str) -> str:
    """Return the content for ONBOARDING.md."""
    return f"""# ONBOARDING — Getting Started with {repo_name}

This template provides a complete governed-skill-workspace architecture.
Follow these steps to set it up in your local environment. For the shortest
beginner path, start with `BEGINNER_GUIDE.md`.

## Prerequisites

- Python 3.11+
- Git
- (Optional) One or more AI coding platforms: Claude Code, Codex, OpenCode, Hermes

## Step 1: Clone

```bash
git clone <your-fork-url>
cd {repo_name}
```

## Step 2: Configure Template Variables

```bash
# Copy template files to real names
cp workspace_manifest.yaml.template workspace_manifest.yaml
cp mcp/configs/installed-local.mcp.json.template mcp/configs/installed-local.mcp.json
cp mcp/configs/wps-agent.mcp.json.template mcp/configs/wps-agent.mcp.json

# Edit each file and replace ${{WORKSPACE_ROOT}}, ${{DATA_ROOT}}, ${{USER_HOME}}
# with your actual local paths. See PATH_MAPPING_REFERENCE.md for details.
```

Or run the conservative helper:

```bash
python scripts/setup_public_workspace.py
```

The helper prepares only the workspace skeleton's own basic functions. It does
not configure provider credentials, AI-platform plugins, or external model
settings.

## Step 3: Install Dependencies

```bash
pip install -r scripts/requirements-context-tools.txt -r scripts/requirements-publish.txt
pip install pytest
```

## Step 4: Verify

```bash
# Run the test suite
python -m pytest scripts/tests -q

# Check workspace health
python scripts/workspace_cli.py health

# List available tasks
python scripts/workspace_cli.py task list

# Explain how a mechanism or path connects to the workspace
python scripts/workspace_cli.py explain mechanism task-routing
python scripts/workspace_cli.py explain path scripts/workspace_cli.py

# View agent registrations
python scripts/workspace_cli.py agent list
```

## Step 5: Register Your Own Skills

See `workspace_manifest.yaml` → `skills[]` for the skill declaration format.
Each skill needs:
1. A unique `id`
2. A `role` (governance, production, maintenance, feedback_diagnosis, runtime_character)
3. An `authority` block defining default and allowed capabilities
4. `execution_modes` specifying write permissions
5. `exposures[]` declaring which platforms can discover the skill

Use `python scripts/workspace_cli.py skill init <id>` to scaffold a new skill.
"""


def write_file(out_dir: Path, rel_path: str, content: str) -> None:
    """Write text content to a file under out_dir."""
    target = (out_dir / rel_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def copy_and_scrub(src_root: Path, out_dir: Path, rel_path: str) -> None:
    """Copy a file, scrubbing its content in transit."""
    src = (src_root / rel_path).resolve()
    content = src.read_text(encoding="utf-8")
    scrubbed = scrub_content(content)
    write_file(out_dir, rel_path, scrubbed)


def strip_skeleton_dir(
    out_dir: Path, rel_path: str, stub_files: list[str], purpose: str
) -> None:
    """Clear a skeleton directory and replace with stub files."""
    target = (out_dir / rel_path).resolve()
    if target.is_dir():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    dir_name = target.name
    for fname in stub_files:
        stub_content = SKELETON_STUB.get(fname, "# {dir_name}\n\nStub file.\n")
        content = stub_content.replace("{dir_name}", dir_name)
        (target / fname).write_text(content, encoding="utf-8")
    if not stub_files:
        # Write a basic README if no stubs specified
        readme = target / "README.md"
        readme.write_text(
            f"# {dir_name}\n\n{purpose}\n\n"
            "This directory is a structural skeleton. "
            "Add your own content following the patterns in the workspace.\n",
            encoding="utf-8",
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a scrubbed public-workspace skeleton."
    )
    parser.add_argument(
        "--out-dir", required=True,
        help="Output directory for the generated public workspace.",
    )
    parser.add_argument(
        "--repo-name", default="governed-skill-workspace-template",
        help="Repository name (used in generated docs).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Only list actions without copying.",
    )
    args = parser.parse_args()

    # Verify we are in the workspace root
    workspace_root = Path.cwd().resolve()
    manifest_path = workspace_root / "workspace_manifest.yaml"
    if not manifest_path.is_file():
        print(
            "ERROR: must be run from workspace root (workspace_manifest.yaml not found).",
            file=sys.stderr,
        )
        return 1

    out_dir = Path(args.out_dir).resolve()
    repo_name = args.repo_name

    print(f"Publishing from: {workspace_root}")
    print(f"Output to:      {out_dir}")
    print(f"Repo name:      {repo_name}")
    print()

    if args.dry_run:
        print("DRY RUN — no files will be written")
        print()

    counts: dict[str, int] = {"copied": 0, "scrubbed": 0, "templated": 0, "stripped": 0}
    warnings: list[str] = []

    # Walk the workspace and process each file
    for dirpath, dirnames, filenames in os.walk(workspace_root):
        # Skip .git
        if ".git" in dirnames:
            dirnames.remove(".git")

        # Compute relative directory
        rel_dir = os.path.relpath(dirpath, workspace_root).replace("\\", "/")
        if rel_dir == ".":
            rel_dir = ""

        # Prune excluded directories early
        top = rel_dir.split("/")[0] if rel_dir else ""
        if top in EXCLUDED_PATHS or rel_dir in EXCLUDED_PATHS:
            dirnames.clear()
            continue

        # Prune skeleton directories (we handle them separately)
        skip_dir = False
        for sdir, _stub_files, _purpose in SKELETON_DIRS:
            if rel_dir == sdir or rel_dir.startswith(sdir + "/"):
                skip_dir = True
                break
        if skip_dir:
            dirnames.clear()
            continue

        for fname in filenames:
            rel_path = (rel_dir + "/" + fname) if rel_dir else fname

            if should_exclude(rel_path):
                continue

            src_file = Path(dirpath) / fname
            rel_path_norm = rel_path.replace("\\", "/")

            if args.dry_run:
                # Classify what would happen
                if needs_scrub(rel_path_norm):
                    kind = "SCRUB"
                elif is_template(rel_path_norm):
                    kind = "TEMPLATE"
                else:
                    kind = "COPY"
                # Check skeleton
                sdir_purpose = is_skeleton_dir(rel_path_norm)
                if sdir_purpose:
                    kind = "STRIP"
                print(f"  [{kind}] {rel_path_norm}")
                continue

            # Check if this file falls inside a skeleton directory
            # (files IN skeleton dirs are excluded)
            in_skeleton = False
            for sdir, _stub_files, _purpose in SKELETON_DIRS:
                if rel_path_norm.startswith(sdir + "/"):
                    in_skeleton = True
                    break
            if in_skeleton:
                continue

            # Copy with or without scrubbing
            if needs_scrub(rel_path_norm):
                try:
                    copy_and_scrub(workspace_root, out_dir, rel_path_norm)
                    counts["scrubbed"] += 1
                except (OSError, UnicodeDecodeError) as exc:
                    warnings.append(f"Failed to scrub {rel_path_norm}: {exc}")
                    # Fall back to direct binary copy
                    try:
                        target = (out_dir / rel_path_norm).resolve()
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_file, target)
                        counts["copied"] += 1
                    except OSError as exc2:
                        warnings.append(f"Failed to copy {rel_path_norm}: {exc2}")
            else:
                try:
                    target = (out_dir / rel_path_norm).resolve()
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, target)
                    counts["copied"] += 1
                except OSError as exc:
                    warnings.append(f"Failed to copy {rel_path_norm}: {exc}")

    # Handle template file generation (create .template variants)
    if not args.dry_run:
        for tf in TEMPLATE_FILES:
            template_rel = tf + ".template"
            tf_norm = tf.replace("\\", "/")
            src_file = workspace_root / tf_norm
            if not src_file.is_file():
                warnings.append(f"Template source not found: {tf_norm}")
                continue
            try:
                content = src_file.read_text(encoding="utf-8")
                scrubbed = scrub_content(content)
                write_file(out_dir, template_rel, scrubbed)
                counts["templated"] += 1
            except OSError as exc:
                warnings.append(f"Failed to create template {template_rel}: {exc}")

    # Handle skeleton directories
    if not args.dry_run:
        for sdir, stub_files, purpose in SKELETON_DIRS:
            strip_skeleton_dir(out_dir, sdir, stub_files, purpose)
            counts["stripped"] += 1

    # Generate metadata documents
    if not args.dry_run:
        write_file(out_dir, "PATH_MAPPING_REFERENCE.md", generate_path_mapping_md())
        write_file(out_dir, "BEGINNER_GUIDE.md", generate_beginner_guide_md(repo_name))
        write_file(out_dir, "ONBOARDING.md", generate_onboarding_md(repo_name))
        write_file(out_dir, "scripts/setup_public_workspace.py", generate_public_setup_py())
        counts["copied"] += 4

    print()
    if args.dry_run:
        print("DRY RUN complete.")
        return 0

    # Git init
    git_dir = out_dir / ".git"
    if not git_dir.is_dir():
        try:
            subprocess.run(
                ["git", "init", "-b", "main"],
                cwd=out_dir,
                capture_output=True,
                check=True,
            )
            # Create .gitattributes from workspace root
            gitattrs_src = workspace_root / ".gitattributes"
            if gitattrs_src.is_file():
                shutil.copy2(gitattrs_src, out_dir / ".gitattributes")
            # Create .gitignore from workspace root
            gitignore_src = workspace_root / ".gitignore"
            if gitignore_src.is_file():
                shutil.copy2(gitignore_src, out_dir / ".gitignore")
            subprocess.run(
                ["git", "add", "."],
                cwd=out_dir,
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "commit", "-m",
                 f"Initial public release: {repo_name}\n\n"
                 "Auto-generated from governed-skill-workspace monorepo.\n"
                 "See PATH_MAPPING_REFERENCE.md for onboarding.\n\n"
                 "Excludes: skills/, agent configs, business code, machine paths."],
                cwd=out_dir,
                capture_output=True,
                check=True,
            )
            counts["git_init"] = 1
        except subprocess.CalledProcessError as exc:
            warnings.append(
                f"Git init failed (stderr): {exc.stderr.decode() if exc.stderr else 'unknown'}"
            )

    print(f"Copied:   {counts.get('copied', 0)} files")
    print(f"Scrubbed: {counts.get('scrubbed', 0)} files")
    print(f"Templated:{counts.get('templated', 0)} files")
    print(f"Stripped: {counts.get('stripped', 0)} skeleton dirs")
    print(f"Git init: {'yes' if counts.get('git_init') else 'already existed'}")
    if warnings:
        print()
        print("Warnings:")
        for w in warnings:
            print(f"  (!) {w}")
    print()
    print(f"Done. Output at: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
