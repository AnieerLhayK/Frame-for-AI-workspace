# Usage Guides

`USAGE_GUIDES/` contains platform loading notes, workspace CLI onboarding, and three public template guides. Skill behavior and authority live in `packages/` and `skills/`; paths and projections are defined by `workspace_manifest.yaml`.

## Start here

- Codex: [quick start](QUICK_START/codex.md)
- Claude Code: [project switching](QUICK_START/claude_code.md)
- OpenCode: [quick start](QUICK_START/opencode.md)
- Hermes: [quick start](QUICK_START/hermes.md)
- Workspace maintenance: [CLI guide](QUICK_START/workspace_cli.md)

## Public workspace template guides

These source files retain the existing publishing contract and generate root-level public documents:

- [Beginner guide](QUICK_START/beginner_guide.md)
- [Onboarding](QUICK_START/onboarding.md)
- [Path mapping reference](QUICK_START/path_mapping_reference.md)

`workspace_manifest.yaml` is the path and projection source of truth. Shared protocols live in `shared/`; current project state and task routing live in `PROJECT_CONTEXT/`.
