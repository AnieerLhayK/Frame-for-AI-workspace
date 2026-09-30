# Style Alignment Notes

Style alignment is a maintenance problem, not just a prompt problem.

## AI Flavor Sources

AI flavor often comes from tidy summaries, excessive balance, generic empathy, symmetrical paragraphs, and safe abstraction.

## Summary Tone

Summaries can flatten voice when they over-explain intent or turn lived style into labels. Use summaries as orientation, not as a replacement for examples.

## Emotional Over-Explanation

Explaining every emotional beat can make output feel synthetic. Some style work requires omission, timing, and restraint.

## Over-Symbolization

Turning recurring motifs into explicit symbols can damage natural voice. Pattern recognition should not force symbolic explanation into every output.

## Rhythm Collapse

Style drift often appears as repeated sentence lengths, predictable transitions, and uniform paragraph cadence.

## Style Drift

Drift can come from prompt changes, missing references, over-generalized corrections, or platform-specific behavior.

## Imitation Risks

References help, but copying surface phrasing can create brittle imitation. The better target is controllable rhythm, stance, texture, and constraint.

## References vs Copying

Use references to learn boundaries and tendencies. Do not treat them as text to reproduce unless the user explicitly asks and rights/permissions allow it.

---

## Workspace Coding And Script Style

These rules govern how governance and maintenance scripts should be written in this workspace.

### General

- Prefer Python standard library for workspace governance scripts.
- Keep PowerShell scripts conservative and explicit.
- Read `workspace_manifest.yaml` before assuming paths.
- Keep workspace-internal paths workspace-relative when practical.
- Keep local absolute deployment paths centralized in the manifest.

### Safety

- Prefer dry-run analysis before filesystem mutation.
- Do not move workspace directories automatically.
- Do not rebuild junctions without explicit approval.
- Do not copy `shared/` into skill folders.
- Do not perform full-drive searches.
- Do not use unbounded parent traversal.
- Do not silently fall back to guessed or historical paths.
- Do not fabricate replacement paths.

### Validation Behavior

- Critical missing resources should produce non-zero exit codes.
- Optional missing resources should produce warnings and degraded mode.
- Validators should catch core drift without enforcing identical prose in every document.
- Reports must include snapshot headers when they are important workspace reports.

### Editing Behavior

- Keep skill core behavior unchanged unless explicitly asked.
- Prefer narrow documentation updates for governance work.
- Use `apply_patch` for manual edits.
- Run `git diff` before reporting completion.

