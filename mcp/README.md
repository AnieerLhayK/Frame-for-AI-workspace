# MCP Workspace

This directory stores local Model Context Protocol servers, client configuration snippets, logs, and downloaded archives.

## Layout

- `servers/`: MCP server source trees and per-server virtual environments.
- `configs/`: reusable MCP client configuration snippets.
- `downloads/`: downloaded archives or installer artifacts.
- `logs/`: local MCP notes or runtime logs when a server supports custom log paths.

## Installed Servers

### wps-agent

- Source: `${WORKSPACE_ROOT}\mcp\servers\wps-agent`
- Virtual environment: `${WORKSPACE_ROOT}\mcp\servers\wps-agent\.venv`
- Client config snippet: `${WORKSPACE_ROOT}\mcp\configs\wps-agent.mcp.json`
- Entry point: `${WORKSPACE_ROOT}\mcp\servers\wps-agent\mcp_server.py`

Use this server for WPS Office document automation through MCP. It supports WPS Word, Excel, and PPT through COM automation when WPS is installed and registered, plus offline `.docx` operations that do not require WPS to be running.

### Additional Local Servers

- `filesystem`: `${WORKSPACE_ROOT}\mcp\servers\filesystem`
- `memory`: `${WORKSPACE_ROOT}\mcp\servers\memory`
- `sequential-thinking`: `${WORKSPACE_ROOT}\mcp\servers\sequential-thinking`
- `playwright`: `${WORKSPACE_ROOT}\mcp\servers\playwright-mcp`
- `context7`: `${WORKSPACE_ROOT}\mcp\servers\context7`
- `hermes`: `${DATA_ROOT}/hermes\hermes-agent\venv\Scripts\hermes.exe mcp serve`

`hermes` is a bridge server that lets MCP-capable agents inspect Hermes conversations and send messages through active Hermes platform connections.

Combined local config snippet:

- `${WORKSPACE_ROOT}\mcp\configs\installed-local.mcp.json`

## Client Registration

The local MCP servers are intended to be registered in each compatible client's
own MCP configuration so its MCP interface can list and use them.

Currently registered locally:

- Codex: user/global MCP config via `codex mcp add`
- Claude Code: user MCP config via `claude mcp add --scope user`
- OpenCode: user config under `${USER_HOME}/.config/opencode` and data under
  `${USER_HOME}/.local/share/opencode`; both are junction-backed by
  `${DATA_ROOT}/opencode`.
- Reasonix: user config at `${USER_HOME}\AppData\Roaming\reasonix\config.toml` (Junction-backed D-drive storage)
- Cursor: global MCP config at `${USER_HOME}/.cursor\mcp.json` (Junction-backed D-drive storage)
- Hermes: client-side MCP config under `${DATA_ROOT}/hermes\config.yaml`

Runtime configs are intentionally not tracked in this workspace because they can contain tokens, local state, and machine-specific paths. Track only these reusable templates and notes.

### GitHub Official MCP

- Source snapshot: `${WORKSPACE_ROOT}\mcp\servers\github-mcp-server\source`
- Config templates: `${WORKSPACE_ROOT}\mcp\configs\github-official.mcp.json`

The official GitHub MCP server is normally used through GitHub's remote MCP endpoint or a Docker image. This machine does not currently have Docker or Go available, so do not claim a local executable is installed until one of those runtimes is explicitly installed.

## Storage Notes

`${USER_HOME}/.codex`, `${USER_HOME}/.claude`,
`${USER_HOME}/.config/opencode`,
`${USER_HOME}/.local/share/opencode`, `${USER_HOME}/.cursor`,
`${USER_HOME}/AppData/Roaming/Cursor`, and Reasonix's managed data
directories point to D-drive storage through junctions or symbolic links.

OpenCode state and cache paths remain separate runtime locations reported by
`opencode debug paths`; do not infer that every OpenCode user directory is
redirected to `${DATA_ROOT}`.

`${USER_HOME}/.claude.json` is a single file, so directory Junctions do not apply. A file symlink would require an elevated shell on this machine.

Do not place MCP server caches or large runtime data on `C:`. Prefer D-drive venvs, package caches, and downloaded archives.
