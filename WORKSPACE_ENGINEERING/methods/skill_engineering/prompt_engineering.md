# Prompt Engineering Notes

These notes record prompt structures that have reduced drift during workspace maintenance.

## Explicit Task Boundary

Clear task boundaries prevent agents from solving adjacent problems by accident. A good boundary names the allowed files, forbidden files, and expected final report.

## Allowed vs Forbidden Changes

Separating allowed and forbidden changes gives the agent a concrete risk map. It is especially useful when source directories, projections, Git history, and generated reports are close together.

## Source-Of-Truth Reminder

Prompts should say which layer wins when context conflicts. In this workspace, `workspace_manifest.yaml`, `shared/`, current source files, and Git state are stronger than old reports or old conversation memory.

## No Automatic Commit

Commit control belongs to the user unless the user explicitly asks for a commit. This keeps review and batching decisions human-owned.

## Do Not Fabricate

"Do not invent paths, reports, or prior results" is important because governance work often has plausible-looking missing artifacts. Missing should be reported as missing.

## Bounded Discovery

Path discovery should be described as bounded. Otherwise agents may search too broadly or infer a wrong workspace from old context.

## Report Snapshot Headers

Reports need snapshot headers because they age. A header tells future readers when, where, by whom, and against which commit the report was produced.

## Final Reply Structure

When a prompt asks for a final structure, the response becomes easier to audit. This matters for governance tasks where the user needs to decide whether to commit.

## Prompts That Cause Scope Explosion

- "Clean up everything."
- "Make it production-ready" without boundaries.
- "Refactor this workspace" without forbidden changes.
- "Fix all drift" without defining drift layers.

## Prompts That Cause Over-Refactor

- Asking for architecture improvement without naming files.
- Combining validator work, migration work, and skill behavior changes in one pass.
- Treating documentation inconsistency as permission to rewrite behavior.

## Prompts That Cause Hallucinated Structure

- Referring to old paths without re-stating current source root.
- Asking for reports without saying to mark missing reports as missing.
- Assuming templates or schemas already exist.

## Prompts That Cause Dangerous Automation

- Asking to migrate paths without dry-run.
- Asking to rebuild links without explicit approval.
- Asking to "sync" platform directories without saying projection surfaces are not source.
- Asking to generalize one runtime fix to all future generated skills.

