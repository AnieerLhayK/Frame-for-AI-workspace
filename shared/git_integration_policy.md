# Conservative Git Integration Policy

Run `workspace merge check <target>` from an isolated branch or worktree before an intentional merge. The check is read-only and compares both tips with their merge-base.

- Only path-disjoint changes are `SAFE_TO_CONTINUE` automatically.
- Any shared path, rename/delete interaction, structured configuration, task record, or ledger-entry overlap is `STOP`; preserve the branch and ask the responsible object or workspace owner to arbitrate.
- Never resolve JSON/YAML, manifests, registries, task records, or generated outputs by choosing a side or joining fields. Rebuild generated outputs from accepted sources.
- After a human-resolved merge, run `git diff --check`, the relevant validator, and `workspace workflow check <task-id>`. A failed required check means the merge is not accepted.
- Record non-trivial arbitration and validation evidence in the existing task ledger and task outcome record. To abandon a preflight or failed merge, discard the isolated branch/worktree; the target branch is unchanged.
