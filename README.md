# Frame-for-AI-workspace

This repository is a deployable framework template for a governed AI workspace.
It contains architecture, policies, routing tools, and portable setup helpers.
Use `workspace_manifest.yaml` to configure paths and authority.

## Extensions

- `skills/`: add skills developed for your workspace.
- `external-skills/`: add reviewed third-party skills.
- `mcp/`: keep reusable configuration templates for MCP connections.
- `packages/`: organize related skills, policies, and implementation by domain.

The extension directories contain guidance or configuration templates for the
components you choose to add.

## Start

```bash
python scripts/setup_public_workspace.py
python -m scripts.workspace.workspace_cli health
python -m pytest scripts/tests -q
```

Read `BEGINNER_GUIDE.md` and `PATH_MAPPING_REFERENCE.md` before adding local
skills or platform integrations. Keep credentials and private source outside
this repository.

