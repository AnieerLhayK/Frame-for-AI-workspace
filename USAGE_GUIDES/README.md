# Usage Guides

`USAGE_GUIDES/` is the prompt-first usage layer for this workspace.

Use this folder when you want to run a skill, copy a safe prompt template, understand where a skill is currently exposed, or follow a cross-platform workflow.

## Start Here

1. Open `START_HERE.md`.
2. Open `QUICK_START/workspace_cli.md` when maintaining or developing the workspace.
3. Check `prompt_registry.yaml` when you need a reusable prompt id or task-specific prompt frame.
4. Copy a prompt from `PROMPT_TEMPLATES/`.
5. Check `QUICK_START/` if you are unsure which platform to use.
6. Open `REFERENCE/README.md` when you need detailed role or workflow guidance.

## What This Is

- A low-maintenance user guide layer.
- A prompt template library.
- A prompt registry for reusable prompt ids and meta-prompts.
- A practical usage map organized by runtime and engineering role, with
  separate platform loading guidance where deployment details differ.
- A place for safe invocation patterns.

## What This Is Not

- Not the source of truth. That remains `workspace_manifest.yaml`.
- Not the protocol layer. Protocols live in `shared/`.
- Not current project memory. That lives in `PROJECT_CONTEXT/`.
- Not runtime drift records. Those live in `packages/character-system/reports/runtime-loop/`.

## Main Entry Points

- `PROMPT_TEMPLATES/`: copy-ready prompts.
- `prompt_registry.yaml`: prompt id registry for task routing, reusable meta-prompts, and template lookup.
- `QUICK_START/`: short platform usage notes.
- `QUICK_START/workspace_cli.md`: beginner guide for the unified maintenance CLI.
- `REFERENCE/README.md`: index of detailed guidance by role and workflow.
- `REFERENCE/runtime/`: user-facing runtime skill details.
- `REFERENCE/engineering/`: generation, diagnosis, maintenance, and lifecycle details.
- `REFERENCE/workflows/`: end-to-end workflows that cross multiple roles.
- `REFERENCE/platforms/`: platform-specific loading and safety notes.
- `SAFETY.md`: compact guardrails for avoiding common misuse.
