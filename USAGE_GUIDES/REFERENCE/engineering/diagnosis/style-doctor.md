# style-doctor Reference

## Purpose

`style-doctor` diagnoses runtime style drift. It names the failure mode, failed layer, evidence, severity, and recommended patch scope.

## Outputs

- Diagnosis packet.
- Handoff packet when maintainer work is needed.

## Boundaries

- It does not patch files.
- It does not create patch notes, validation notes, or generalization notes.
- It does not update the patch ledger.
- It does not decide accepted/rejected/deferred.
- It does not update generator templates.
- It does not decide generator generalization.
- Its handoff file recommendations should use workspace-relative source paths,
  not platform projection paths.
