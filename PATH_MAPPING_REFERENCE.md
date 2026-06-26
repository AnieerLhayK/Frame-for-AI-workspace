# PATH_MAPPING_REFERENCE

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
