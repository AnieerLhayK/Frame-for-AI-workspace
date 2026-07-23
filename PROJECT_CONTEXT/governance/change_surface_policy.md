# Change Surface Policy

Use change-surface planning when one goal could be implemented through several
different file sets.

Do not invoke it mechanically for every task. A resolved task with one obvious
owner and one narrow target should proceed directly.

The planner does not decide behavior from filenames alone. It combines:

- an exact task id and resolved `write_scope`;
- an explicit change intent;
- source, registry, protocol, tooling, documentation, memory, report, and
  projection layer rules;
- optional candidate sets supplied as named alternatives.

## Decision Order

1. Reject paths outside the resolved write scope.
2. Reject absolute platform paths and projection surfaces as source edit targets.
3. Reject generated reports as substitutes for owning source changes.
4. Prefer the narrowest option containing the owning layer for the declared intent.
5. Use documentation, memory, and refreshed snapshots as supporting changes only
   when the source change makes them necessary.
6. Inspect call sites and validation impact when two viable options remain close.

## Intent Contract

- `behavior`: skill source first.
- `metadata`: skill source metadata or the canonical registry.
- `exposure`: manifest and projection tooling, with external changes separately authorized.
- `routing`: task or prompt registries.
- `tooling`: scripts and their focused tests.
- `policy`: the narrowest owning shared policy or canonical registry.
- `documentation`: user-facing guides first.
- `report`: generated snapshot output through its generator.
- `migration`: canonical path registry and migration tooling.
- `architecture`: manifest, shared policy, and affected source contracts.

The recommendation identifies the layer to inspect first. It does not authorize
editing every path in that layer and does not replace evidence from call sites,
tests, manifests, or the target file's nearest owning policy.

## Post-Change Verification

Planning compares candidate paths before editing. Verification compares the
resolved task scope with current Git evidence after editing:

```powershell
workspace changes verify <task-id>
```

The verifier reads unstaged, staged, and untracked paths by default. It marks
high-risk changes but permits them when the task explicitly declares the path.
It never reverts, deletes, cleans, stages, commits, or moves a file.

Risk classification is owned by `shared/agent_governance.yaml`, reusing the
existing surface classes rather than creating a parallel permission system.
The verifier reports `normal`, `elevated`, or `high`, plus affected surfaces,
confirmation requirements, and worktree recommendations. High risk is a review
signal, not an automatic denial when the task declares the path.

For the normal post-edit check, use:

```powershell
workspace workflow check <task-id>
```

This resolves the task, verifies actual Git paths, runs unstaged and staged
`git diff --check`, and lists routed validation commands. It does not run the
tests, stage changes, commit, push, switch branches, or modify files.

- `PASS`: every actual path is inside a concrete resolved write scope.
- `WARNING`: verification is incomplete because the task contains declarative
  scopes that cannot be reduced to exact paths.
- `ERROR`: actual changes are outside scope, high-risk changes are undeclared,
  or task/Git resolution failed.

On ERROR, preserve the work and stop expanding it. Select a better task,
transfer the result to a new task or safety branch, manually select legal
changes, or isolate high-risk work in a worktree.
