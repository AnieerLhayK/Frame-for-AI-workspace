# Handoff Format

This document standardizes how runtime feedback becomes maintainer-actionable maintenance work across compatible agent platforms.

## Runtime Feedback Packet

```text
title:
character_id:
reported_by:
date:
task_type:
input_excerpt:
output_excerpt:
feedback:
expected_behavior:
suspected_drift:
attachments_or_paths:
```

## Maintainer Packet

The agent invoking `character-maintainer` should convert the feedback into:

```text
issue_summary:
character_id:
reproduction_context:
diagnosis:
failed_layer:
patch_plan:
target_files:
validation_steps:
risk:
version_note:
```

## Evidence Rules

- Include short excerpts only when needed.
- Prefer local file paths over pasted full files.
- Separate observed failure from proposed fix.
- Mark uncertain diagnosis as uncertain.

## Path Rules

Use manifest-resolved workspace paths as source of truth:

```text
workspace-relative/path
shared-relative/path
skill-relative/path
```

Do not ask maintainers to edit platform link paths directly.
