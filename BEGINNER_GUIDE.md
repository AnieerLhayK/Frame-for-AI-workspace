# BEGINNER_GUIDE - Frame-for-AI-workspace

This repository is a public framework template for building a governed AI
workspace. It keeps the workspace's own structure visible: task routing,
knowledge lookup, agent boundaries, report checks, and explainable CLI
entrypoints. It contains no bundled character-system or existing skills.

## Quick Start

Clone your fork, then run the conservative first-run helper:

```bash
git clone <your-fork-url>
cd Frame-for-AI-workspace
python scripts/setup_public_workspace.py
```

The helper:

- copies `.template` configuration files to their real names when missing;
- replaces standard path variables such as `${WORKSPACE_ROOT}` and `${DATA_ROOT}`;
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

These commands show the framework's own basic functions before you add your
own skills under `skills/` or separately reviewed external skills under
`external-skills/`.

## What To Configure Manually

After the helper runs, review:

- `workspace_manifest.yaml` for your local source root and platform roots;
- `shared/agent_registry.yaml` for per-agent data/cache roots;
- `mcp/configs/*.json` only if you use those MCP servers;
- platform-specific loading surfaces only after you understand the projection
  model in `ARCHITECTURE.md`.

Keep credentials and provider settings out of this repository unless you have a
separate, private policy for them.
