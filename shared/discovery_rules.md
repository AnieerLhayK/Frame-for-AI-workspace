# Discovery Rules

This workspace uses bounded discovery. A skill may discover workspace resources only inside the declared workspace, its own directory ancestry, or platform projections declared by `workspace_manifest.yaml`.

## Discovery Targets

Skills may discover:

- workspace root
- `workspace_manifest.yaml`
- workspace-global `shared/`
- the current skill package's declared shared directory
- manifest-routed protocol documents
- required skill files
- optional support files

Skills must not discover resources by scanning an entire drive.

## Search Order

Use this order:

1. Current skill directory.
2. Parent lookup for `workspace_manifest.yaml`, with a maximum depth of 5 levels.
3. `shared/` under the discovered workspace root.
4. The current skill's `package_id`, resolved through `packages[]`.
5. The package's declared `shared_path` and `protocol_manifest`.

Stop when a required resource is found. If multiple candidates exist, prefer the manifest-declared source path.

## Workspace Root Discovery

Starting from the current skill directory:

1. Check the current directory for `workspace_manifest.yaml`.
2. Move one parent upward.
3. Repeat until the manifest is found or 5 parent levels have been checked.
4. If no manifest is found, emit a required-resource error.

Do not continue above the fifth parent. Do not search `D:\`, user profiles, or unrelated project roots.

The reference bootstrap implementation is:

```powershell
python scripts\bootstrap_workspace.py --start .
```

## Protocol Discovery

After the manifest is found:

1. Resolve `shared.source_path` relative to `workspace.source_of_truth`.
2. Verify that the resolved directory exists.
3. Verify that every required protocol declared in `protocols` exists.
4. If the skill declares `package_id`, resolve that package's `shared_path`.
5. Verify every `skills[].protocol_dependencies` entry against the package protocol manifest.
6. Do not copy protocols from a projection back into source automatically.

## Required Files

Required files are declared by each skill in `skills[].required_files`.

If a required file is missing:

- stop the workflow
- emit a standard `[ERROR]` block
- include the manifest path, expected location, discovery attempts, and action

## Optional Files

Optional files are declared by each skill in `skills[].optional_files`.

If an optional file is missing:

- continue in degraded mode
- emit a `[WARNING]` block
- do not invent replacement content

## Forbidden Discovery

The following are forbidden:

- recursive full-drive scans
- unbounded parent traversal
- silent fallback to guessed paths
- copying shared protocols into skills
- treating platform projections as source of truth
- automatic moves or junction rebuilds during bootstrap
