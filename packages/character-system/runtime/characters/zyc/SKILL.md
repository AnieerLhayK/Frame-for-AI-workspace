---
id: zyc
description: Template skill scaffold (replace with actual skill)
role: production
authority:
  default: read
  allowed:
    - invoke
    - record_write
execution_modes:
  default: text_only
  allowed:
    - text_only
    - record_write
platform: claude
---

# zyc

This is a structural placeholder. Implement your skill following the
patterns defined in workspace_manifest.yaml and shared/agent_governance.yaml.

## Registration

To register this skill, add an entry in workspace_manifest.yaml → skills[]
with the appropriate role, authority, execution_modes, and exposures.
