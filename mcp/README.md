# MCP configuration templates

The `configs/` directory contains reusable client configuration examples:

- `installed-local.mcp.json.template` combines the supported local servers.
- `wps-agent.mcp.json.template` provides a WPS-only entry.
- `github-official.mcp.json` provides the official GitHub server entry.

Install the servers separately in an external runtime directory before using
these examples. Replace `${DATA_ROOT}`, `${WORKSPACE_ROOT}` and `${USER_HOME}`
with your deployment paths, and adjust commands to your installed executables.
The `.cmd` and Python `Scripts` paths in the examples target Windows.

Keep Memory's `MEMORY_FILE_PATH` outside dependency directories so reinstalling
packages preserves its data. Configure `WPS_AGENT_LOG_DIR` for a WPS installation
that supports this variable; log rotation belongs to that installation.
Review arguments, environment variables and client permissions before enabling
any server. These examples do not install dependencies or configure clients.
