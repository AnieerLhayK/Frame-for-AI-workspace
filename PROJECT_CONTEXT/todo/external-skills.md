# External Skill Compatibility Queue

This is the intake queue for raw external skill repositories under
`workspace_manifest.yaml -> external_roots.raw_skills`. Add a row as soon as a
new source appears, before detailed evaluation. A source may leave this queue
only when its status and next action are recorded.

## Lifecycle

`discovered` → `provenance-review` → `compatibility-review` → `adaptation`
→ `validation` → `registered` → `exposed`

Every entry should record the source URL or local origin, commit/tag, license
and attribution status, candidate functions, workspace conflicts, adaptation
decision, validation result, and next action. Raw research copies stay outside
the workspace; adapted source belongs under `external-skills/<function>/`.
Raw snapshots intentionally omit `.git` history; the recorded commit/tag is
the provenance marker for the snapshot that was obtained.

## Current Queue

| Source | Location / revision | Candidate function | Status | Next action |
| --- | --- | --- | --- | --- |
| `alemtuzlak/skills` | `${WORKSPACE_ROOT}/research/skills/alemtuzlak-skills` @ `ab1c074` | compatibility review | discovered | inspect skill inventory, provenance, and overlap with current contracts |
| `mattpocock/skills` | `${WORKSPACE_ROOT}/research/skills/mattpocock-skills` @ `391a270` | engineering, productivity | partial-exposure | continue reviewing the remaining source; `teach` is deferred pending a workspace-specific teaching-project adapter |

## Deployed Slice — 2026-07-13

The following candidates were copied from the raw snapshot into the curated
workspace layer, adapted for workspace context/policy, registered in the
manifest, and exposed to both Codex and Claude Code:

- `external-skills/productivity/grill-me`
- `external-skills/productivity/grilling`
- `external-skills/productivity/handoff`
- `external-skills/engineering/diagnosing-bugs`
- `external-skills/engineering/tdd`
- `external-skills/engineering/code-review`
- `external-skills/engineering/codebase-design`
- `external-skills/engineering/writing-great-skills`

All eight are constrained to `text_only`; they provide process guidance and do
not grant source, record, environment, or platform-write authority. The
`code-review` instructions were changed to remove the source repository's
`/setup-matt-pocock-skills` dependency. The `handoff` instructions point
transient output to the configured staging directory.

`productivity/teach` remains raw-only for now. It is a stateful teaching
workspace that expects `MISSION.md`, `RESOURCES.md`, `NOTES.md`, reference
HTML, lesson HTML, learning records, and assets; exposing it without an
adapter would make it write against the wrong project model.

## Completion Record

Do not delete completed entries. Mark them `registered`, `exposed`, `deferred`,
or `rejected` with a short reason and link to the adapted source or decision
record. This preserves why a raw source was or was not internalized.
