# Reference Guide

Use this index after the quick start or prompt registry has identified what you
are trying to do. Read only the section needed for the current task.

This layer explains responsibilities, boundaries, and selection criteria. It is
not the copy-ready prompt layer. When you need text to paste into an AI session,
use `../PROMPT_TEMPLATES/` or resolve a prompt id through
`../prompt_registry.yaml`.

## Runtime

Open `runtime/` when using a user-facing skill or deciding whether observed
output should be handed off for diagnosis or maintenance.

## Engineering

Open `engineering/` when generating, diagnosing, maintaining, or evolving a
skill. The subdirectories identify engineering responsibility:

- `generation/`: create or update generated skill artifacts from authorized inputs.
- `diagnosis/`: inspect output and produce bounded evidence or handoff packets.
- `maintenance/`: patch an existing skill without taking over generator ownership.

Use `engineering/production-maintenance-relationships.md` when more than one
engineering role could plausibly own the change.

## Workflows

Open `workflows/` for end-to-end procedures that cross runtime and engineering
roles, including generation, drift diagnosis, patching, validation, and
generator generalization.

## Platforms

Open `platforms/` only for platform-specific loading and safety details.
Platform exposure determines where a skill is visible; it does not determine
the skill's source ownership or modification authority.

For canonical source paths and active exposures, consult
`workspace_manifest.yaml` rather than copying path facts into this guide.

When this guide and a prompt template cover the same workflow, keep this guide
short and explanatory. Put detailed step-by-step guardrails in the matching
template.
