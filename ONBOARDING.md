# ONBOARDING — Getting Started with Frame-for-AI-workspace

This template provides a complete governed-skill-workspace architecture.
Follow these steps to set it up in your local environment.

## Prerequisites

- Python 3.11+
- Git
- (Optional) One or more AI coding platforms: Claude Code, Codex, OpenCode, Hermes

## Step 1: Clone

```bash
git clone <your-fork-url>
cd Frame-for-AI-workspace
```

## Step 2: Configure Template Variables

```bash
# Copy template files to real names
cp workspace_manifest.yaml.template workspace_manifest.yaml
cp mcp/configs/installed-local.mcp.json.template mcp/configs/installed-local.mcp.json
cp mcp/configs/wps-agent.mcp.json.template mcp/configs/wps-agent.mcp.json

# Edit each file and replace ${WORKSPACE_ROOT}, ${DATA_ROOT}, ${USER_HOME}
# with your actual local paths. See PATH_MAPPING_REFERENCE.md for details.
```

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
python scripts/resolve_task_context.py --list

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
