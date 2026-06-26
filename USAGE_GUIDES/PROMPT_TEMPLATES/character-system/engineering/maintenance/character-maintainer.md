# character-maintainer Prompt Templates

Current default exposure: Codex. Source patches still require the maintainer authority and `source_patch` mode.

## Quick Patch From Diagnosis

```text
Use character-maintainer.

Target character:
<path to character folder>

Diagnosis or handoff:
<path, id, or pasted packet>

Task:
Review the diagnosis, inspect the current source files, and decide accepted / rejected / deferred before editing.

Guardrails:
- Treat any source diff produced by style-doctor as candidate patch material only.
- Do not assume doctor changes are approved.
- Do not modify character-generator.
- Patch only the smallest responsible surface if accepted.
- Write/update runtime-loop records only after the maintainer decision.
- Do not commit unless I explicitly ask.
```

## Patch Existing Character From Feedback

```text
Use character-maintainer.

Target character:
<absolute path to character folder>

Feedback:
"<user feedback or observed failure>"

Allowed patch scope:
<files or folders that may be changed>

Do not touch:
<files, folders, or behaviors that must not change>

Validation expectation:
<test prompt, before/after behavior, or acceptance criteria>

Task:
Diagnose first, then patch only the smallest responsible surface.

Guardrails:
- Do not edit character-generator.
- Do not edit generator templates.
- Do not rewrite the whole character.
- Preserve manual evolution and examples unless they directly cause the failure.
- If the lesson may generalize, write a generalization note instead of changing generator assets.
- Show git diff summary and wait for approval before commit.

Required output:
- Diagnosis summary.
- Maintainer decision: accepted, rejected, or deferred.
- Files changed.
- Patch note.
- Validation note or validation summary.
- Generalization recommendation, if any.
```

## Patch From style-doctor Diagnosis

```text
Use character-maintainer.

Target character:
<absolute path to character folder>

Diagnosis source:
<path to diagnosis packet, handoff packet, or pasted diagnosis summary>

Task:
Review the diagnosis, decide accepted/rejected/deferred, and apply a narrow patch only if accepted.

Guardrails:
- Do not modify character-generator in this pass.
- Do not generalize from one character without a generalization note.
- Do not change unrelated files.
- Preserve existing manual refinements.

Runtime loop records:
- Write or update a patch note.
- Write or update a validation note.
- Update the patch ledger when this is a formal runtime-loop case.
- Create a generalization note only if the lesson is plausibly reusable.

Final response:
- Decision.
- Patch summary.
- Validation result.
- Remaining risk.
- Whether a separate generator task should be opened.
```
