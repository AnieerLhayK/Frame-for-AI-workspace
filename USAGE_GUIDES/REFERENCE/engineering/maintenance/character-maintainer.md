# character-maintainer Reference

## Purpose

`character-maintainer` maintains existing character skills. It patches, aligns, validates, and records evolution.

## Inputs

- Target character folder.
- User feedback, diagnosis packet, or handoff packet.
- Allowed patch scope.
- Do-not-touch constraints.
- Validation expectation.

## Expected Behavior

1. Diagnose first.
2. Decide accepted, rejected, or deferred.
3. Patch the smallest responsible surface.
4. Record patch reason and expected effect.
5. Validate.
6. Recommend generalization only when justified.

## Boundaries

- Do not create new characters.
- Do not rewrite whole characters by default.
- Do not directly modify `character-generator`.
- Do not generalize from a single character without a generalization note.
