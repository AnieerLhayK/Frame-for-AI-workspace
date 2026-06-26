# Failure Policy

This workspace separates required resources from optional resources. Missing resources must be reported explicitly.

## Required Resources

Required resources include:

- `workspace_manifest.yaml`
- workspace protocols declared as required in the manifest
- package protocols declared by `skills[].protocol_dependencies`
- each skill `SKILL.md`
- each skill `README.md`
- critical prompts and references declared in `skills[].required_files`
- required platform projections declared in `projections[]`

Missing required resources must stop the workflow.

## Optional Resources

Optional resources include:

- reports
- examples
- runtime history
- archived notes
- generated packages
- private local shortcuts
- tests that are not required for runtime discovery

Missing optional resources may continue in degraded mode after a warning.

## Error Reporting Standard

Use this format for required failures:

```text
[ERROR]
Missing required resource:
<resource-id-or-relative-path>

Expected:
<manifest-resolved-location>

Discovery attempts:
- <attempt 1>
- <attempt 2>
- <attempt 3>

Action:
restore the missing resource
or update workspace_manifest.yaml if the location intentionally changed
```

Use this format for optional failures:

```text
[WARNING]
Missing optional resource:
<resource-id-or-relative-path>

Expected:
<manifest-resolved-location>

Impact:
continuing in degraded mode; related reports, examples, or history may be unavailable
```

## No Silent Fallback

Fallbacks must be visible. If a workspace or package protocol cannot be
resolved from its manifest-declared source, stop rather than silently borrowing
another package's protocol or a platform projection.

## No Fabricated Paths

Do not invent replacement paths. If the manifest does not declare a source, projection, or protocol path, stop and ask for manifest maintenance instead of guessing.

## Bootstrap Failure

If bootstrap discovery cannot find `workspace_manifest.yaml` within the configured parent depth, report every attempted path and stop. Do not continue by scanning a drive root or by guessing historical workspace locations.
