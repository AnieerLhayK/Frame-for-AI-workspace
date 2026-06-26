# zyc Reference

## Purpose

`zyc` is a runtime character skill. Its current platform exposures are declared
in `workspace_manifest.yaml` and do not change its text-only authority.

## Use

Use it for supported runtime writing tasks such as rewrite, continuation, critique, and style transfer according to its own skill instructions.

## Drift Handling

If output drifts:

1. Use `style-doctor` to diagnose.
2. Create diagnosis and handoff records when needed.
3. Let `character-maintainer` patch the source character.
4. Do not generalize ZYC-specific changes into generator defaults without review.
