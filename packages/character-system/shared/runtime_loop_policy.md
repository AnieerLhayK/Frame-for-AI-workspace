# Runtime Loop Policy

This policy defines how runtime character failures become durable, reviewable, and auditable workspace records.

## Purpose

The runtime loop turns live character failures on any compatible platform into traceable maintenance evidence:

```text
runtime character failure
-> style-doctor diagnosis
-> handoff packet
-> character-maintainer decision
-> patch note
-> validation note
-> optional generator generalization note
-> ledger update
```

The goal is not to automate every decision. The goal is to make every runtime drift recoverable, explainable, and reviewable after the fact.

## Roles

- `style-doctor`: diagnoses runtime drift, identifies the failed layer, records evidence, writes diagnosis packets, and creates handoff packets when maintenance is needed.
- `character-maintainer`: reviews handoffs, decides `accepted`, `rejected`, or `deferred`, applies narrow patches when accepted, records patch notes and validation notes, and updates ledgers.
- character skill: remains the source artifact being diagnosed or patched. Character-specific manual evolution must be preserved unless it directly causes the failure.
- `character-generator`: receives only reviewed generalization lessons. It must not be changed directly from one character's runtime failure or patch.

## Authority Boundaries

`style-doctor` may create diagnosis packets, handoff packets, and diagnosis-ledger entries for formal diagnosis events.

`style-doctor` must not:

- edit character source files;
- edit generator, maintainer, shared protocol, or manifest files;
- create patch notes, validation notes, or generalization notes;
- update `packages/character-system/reports/runtime-loop/ledgers/patch_ledger.md`;
- mark a maintainer decision such as `accepted`, `rejected`, or `deferred`;
- mark patch state such as `applied`, `validated`, or `closed`.

Patch suggestions from `style-doctor` are candidate patch text only. They become workspace changes only after `character-maintainer` reviews the linked diagnosis/handoff and records a decision.

If a model or platform cannot enforce this boundary reliably, it should output diagnosis and handoff packet text only rather than writing files.

Handoff packets should recommend workspace-relative source paths. Platform projection paths are runtime deployment details and should not be used as maintainer edit targets.

## ID Rules

IDs are manually writable and script-friendly. Use the local date of record creation.

```text
Diagnosis ID:      DIAG-YYYYMMDD-001
Handoff ID:        HANDOFF-YYYYMMDD-001
Patch ID:          PATCH-YYYYMMDD-001
Validation ID:     VAL-YYYYMMDD-001
Generalization ID: GEN-YYYYMMDD-001
```

Increment the final number for each record type created on the same date. Records should cross-reference related IDs instead of relying on filename order.

## Record Naming And No-Overwrite Rule

Runtime-loop records must use unique filenames. Do not write durable diagnosis or handoff records to fixed names such as `latest.md`, `diagnosis.md`, `handoff.md`, or `output.md`.

Use the ID, local timestamp, character id, and case/task slug in the filename:

```text
packages/character-system/reports/runtime-loop/diagnoses/DIAG-YYYYMMDD-001-HHMMSS-<character-id>-<case-or-task>.md
packages/character-system/reports/runtime-loop/handoffs/HANDOFF-YYYYMMDD-001-HHMMSS-<character-id>-<case-or-task>.md
packages/character-system/reports/runtime-loop/patches/PATCH-YYYYMMDD-001-HHMMSS-<character-id>-<case-or-task>.md
packages/character-system/reports/runtime-loop/validations/VAL-YYYYMMDD-001-HHMMSS-<character-id>-<case-or-task>.md
```

Slug rules:

- use lowercase ASCII when possible;
- replace spaces and punctuation with `-`;
- keep it short, for example `zyc-case008-social-critique`;
- if no case exists, use the task type, for example `zyc-runtime-rewrite`;
- if the target filename already exists, do not overwrite it. Increment the sequence or timestamp and write a new record.

Each packet should include its actual `record_path`. Handoff packets should also include the linked `diagnosis_record_path` when available. File names are for durable retrieval; the ID fields inside the packet remain the primary cross-reference.

Before creating a new record, inspect the target directory and the relevant ledger to choose the next ID. In concurrent sessions, prefer creating a new unique record over reusing or editing another session's record.

## Maintainer Record Lookup

`character-maintainer` must not assume the newest diagnosis or handoff is the relevant one.

Lookup order:

1. Use the explicit file path if the user or packet provides one.
2. Use `handoff_id` to locate a handoff, then follow `diagnosis_id` and `diagnosis_record_path`.
3. Use `diagnosis_id` to search `packages/character-system/reports/runtime-loop/diagnoses/` and `packages/character-system/reports/runtime-loop/ledgers/diagnosis_ledger.md`.
4. If only a case/task name is provided, search by character id and case/task slug, then ask the user if multiple candidates match.
5. Verify that the filename ID, packet ID, linked IDs, and ledger status agree before accepting a patch.

If lookup is ambiguous, defer rather than patching from the wrong record.

## Diagnosis Packet Requirements

A diagnosis packet records what failed before any patch is applied. It should include:

- `diagnosis_id`
- `created_at`
- `source_character`
- `source_skill`
- `task_type`
- `user_feedback`
- `failed_output_excerpt`
- `expected_style_direction`
- `drift_types`
- `failed_layer`
- `evidence`
- `severity`
- `suggested_patch_scope`
- `do_not_touch`
- `related_shared_protocols`
- `next_owner`

Store diagnosis packets under `packages/character-system/reports/runtime-loop/diagnoses/` using `packages/character-system/shared/templates/diagnosis_packet.template.md`.

The template path is registered in `packages/character-system/shared/protocol_manifest.json` and checked by `scripts/validate_protocols.py`.

## Handoff Packet Requirements

A handoff packet is created when `style-doctor` believes maintainer review is needed. It should include:

- `handoff_id`
- `diagnosis_id`
- `from`
- `to`
- `character_id`
- `reason_for_handoff`
- `recommended_files_to_inspect`
- `recommended_patch_type`
- `risk_level`
- `acceptance_criteria`
- `deferred_questions`

Store handoff packets under `packages/character-system/reports/runtime-loop/handoffs/` using `packages/character-system/shared/templates/handoff_packet.template.md`.

The runtime-loop templates and ledgers are part of the shared protocol contract and should be revalidated after changes.

## Maintainer Decisions

`character-maintainer` must record one of these decisions in the patch note and patch ledger:

- `accepted`: the failure is valid and a narrow patch should be applied.
- `rejected`: the proposed change is not supported, is unsafe, duplicates existing guidance, or would damage the character.
- `deferred`: more evidence, user input, validation, or cross-file review is needed.

Accepted patches should remain small and should explain why the touched surface is responsible for the failure.

## Patch Validation

After an accepted patch is applied:

1. Re-read the changed file and adjacent source files.
2. Compare the patch against the diagnosis evidence and acceptance criteria.
3. Run any relevant script or prompt-based validation that is safe for the scope.
4. Write a validation note under `packages/character-system/reports/runtime-loop/validations/`.
5. Update `packages/character-system/reports/runtime-loop/ledgers/patch_ledger.md`.

Validation can be qualitative when no automated test exists, but it must state the test prompt, observed improvement, remaining issue, reviewer, and next action.

## Generator Generalization

Write a generator generalization note only when a validated character patch reveals a lesson that may improve future generated characters or shared protocols.

Use `packages/character-system/reports/runtime-loop/generalization_backlog/` and `packages/character-system/shared/templates/generalization_note.template.md`.

A generalization note is appropriate when:

- the same failure can reasonably affect multiple characters;
- the lesson concerns generator scaffolding, shared protocol vocabulary, handoff shape, or default evaluation criteria;
- validation shows the patch helped without relying on highly specific character traits;
- the maintainer can explain the generator-level target and risk.

## When Generalization Is Forbidden

Do not generalize when:

- the evidence is a single weak or ambiguous runtime output;
- the lesson depends on ZYC-specific voice, corpus structure, imagery, rhythm, or manual evolution;
- the patch protects a local exception rather than a reusable rule;
- the change would modify generator templates before maintainer review;
- the patch would flatten mature character differences into one default style;
- the source record lacks diagnosis, patch, or validation evidence.

## Protecting ZYC-Specific Lessons

ZYC is a mature character-specific artifact. Its runtime lessons should default to `character-specific` unless the maintainer explicitly records a generalization candidate with evidence that the lesson applies beyond ZYC.

Never treat ZYC's special structure, pacing, emotional restraint, imagery limits, or handcrafted prompt choices as generator defaults from one patch. Use the generalization backlog for review instead.

## Protecting Manual Evolution

Maintainer patches must not erase handcrafted character evolution. Before patching:

- inspect recent records, reports, and relevant source files;
- prefer additions, clarifications, or narrow replacements;
- avoid template normalization;
- preserve strong examples unless they directly cause the failure;
- record a rollback plan in the patch note.

## Optional Missing Reports

Missing optional reports are not runtime-loop blockers. Treat them as degraded context:

- continue if required source files and shared protocols exist;
- record the missing report as an assumption or evidence gap;
- do not recreate unrelated historical reports just to satisfy a handoff;
- update ledgers and runtime-loop records for the current event.

## Policy Coordination

This policy works with:

- `shared/reporting_policy.md`: runtime-loop records are reports and audit artifacts. They are not stronger than manifest, shared protocols, or Git state.
- `packages/character-system/shared/future_drift_policy.md`: runtime-loop ledgers provide durable evidence for future drift prevention.
- `packages/character-system/shared/patch_protocol.md`: diagnosis and handoff records extend the existing doctor-to-maintainer patch payload.
- `packages/character-system/shared/versioning_policy.md`: patch notes and validation notes satisfy version record expectations for meaningful changes.
- `packages/character-system/shared/protocol_manifest.json`: registry used by `scripts/validate_protocols.py` to verify protocol, template, ledger, and core skill references.

If policies conflict, prefer the narrower source of truth for the action: manifest for paths, shared protocols for workflow rules, and character source files for character behavior.

## State Machines

Diagnosis state:

```text
new -> handed_off -> accepted -> patched -> validated -> closed
```

Allowed alternate terminal or holding states:

```text
rejected
deferred
```

Patch state:

```text
proposed -> accepted -> applied -> validated -> closed
```

Allowed alternate states:

```text
reverted
deferred
```

Generalization state:

```text
candidate -> accepted -> implemented -> validated -> closed
```

Allowed alternate states:

```text
rejected
deferred
```

Ledgers should use these state names when possible so future scripts can parse status consistently.
