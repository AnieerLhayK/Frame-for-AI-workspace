# style-doctor Prompt Templates

Current exposure: OpenCode. Exposure does not permit source patches.

## Safe Text-Only Diagnosis

Use this when the model may be weaker, file access is risky, or you want zero source changes.

```text
Use style-doctor.

Diagnose this runtime drift, but do not write or modify any files.
Output packet text only.

Source character:
<character id, such as zyc>

User feedback:
"<feedback>"

Failed output excerpt:
<excerpt>

Expected style direction:
<what should be different>

Guardrails:
- Do not patch source files.
- Do not update any ledger.
- Do not create patch notes, validation notes, or generalization notes.
- Do not mark accepted/rejected/deferred.
- If maintainer work is needed, include a handoff packet as text only.
```

## Diagnose Runtime Drift

```text
Use style-doctor.

Source character:
<character id, such as zyc>

Source skill path:
<absolute path if known>

Task type:
<rewrite | continuation | imitation | critique | style_transfer | other>

User feedback:
"<feedback>"

Failed output excerpt:
<excerpt>

Expected style direction:
<what should be different>

Task:
Classify the drift, identify the failed layer, and produce a diagnosis packet.

Guardrails:
- Do not patch source files directly.
- Do not create patch notes, validation notes, or generalization notes.
- Do not update `packages/character-system/reports/runtime-loop/ledgers/patch_ledger.md`.
- Do not mark any patch `accepted`, `rejected`, `deferred`, `applied`, or `validated`.
- Do not modify character-generator, character-maintainer, shared protocols, or workspace manifest files.
- Do not generalize character-specific lessons.
- Use workspace-relative source paths in handoff recommendations, not platform projection paths.
- If a maintainer is needed, produce a handoff packet.

Output:
- diagnosis_id
- drift types
- failed layer
- evidence
- severity
- suggested patch scope
- do_not_touch
- next owner
```

## Prepare Handoff To Maintainer

```text
Use style-doctor.

Diagnosis:
<diagnosis packet or summary>

Target maintainer:
character-maintainer

Task:
Create a handoff packet for maintainer review.

Include:
- handoff_id
- diagnosis_id
- character_id
- reason_for_handoff
- recommended_files_to_inspect
- recommended_patch_type
- risk_level
- acceptance_criteria
- deferred_questions

Guardrails:
- Do not patch source files.
- Do not write patch notes, validation notes, or generalization notes.
- Do not edit `packages/character-system/reports/runtime-loop/ledgers/patch_ledger.md`.
- Do not mark accepted/rejected/deferred; that decision belongs to character-maintainer.
- Use workspace-relative source paths in `recommended_files_to_inspect`.
```
