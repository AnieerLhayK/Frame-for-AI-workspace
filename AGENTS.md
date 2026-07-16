# AGENTS.md

This public repository is a governed AI workspace framework template.

## Boundary

- Treat this repository as source for framework structure and policies only.
- Keep credentials, private corpora, personal data, and provider state outside
  the repository.
- `skills/` and `external-skills/` are documentation-only extension layers in
  this release, with no bundled skills.
- Add downstream domain packages only after reviewing provenance, privacy,
  licensing, and deployment boundaries.

## Safe Start

Run `python scripts/setup_public_workspace.py`, then use the read-only health,
task-routing, and test commands documented in `BEGINNER_GUIDE.md`.

The optional Claude model-advice toggle is documented at
`.claude/model-routing-advice.json`; it is advisory and does not grant extra
permissions.
