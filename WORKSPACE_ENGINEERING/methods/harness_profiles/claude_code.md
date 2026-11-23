# Claude Code Harness Profile

Status: reference profile; it does not change DSH's default selection.

## Workspace sources

- `USAGE_GUIDES/QUICK_START/claude_code.md`: local project switching,
  instruction loading and registered launch conventions.
- `.claude/project-boundary.json` and `.claude/rules/`: local Claude-specific
  project isolation inputs. Their meaning must not be assumed to transfer to a
  different host without implementation and testing.
- Root `AGENTS.md` and the Workspace manifest and governance policies: the
  shared source of task, write, delivery and authority requirements.

## Official references

- [Claude Code settings and precedence](https://code.claude.com/docs/en/settings).
- [Claude Code skills](https://code.claude.com/docs/en/skills).

Use these links to investigate the host's current behavior. Settings, hooks and
skills are host-specific; do not assume DSH reproduces their enforcement or
loading order. Validate any adaptation against the selected DSH version.
