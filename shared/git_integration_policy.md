# Conservative Git Integration Policy

Run `workspace merge check main --head <agent-branch> --agent <agent> --record-id <TASK-ID>` before an intentional managed merge. The check is read-only and compares both tips with their merge-base.

## Long-lived Agent branches

Codex and Claude Code write only on their registered `codex` and `claude`
branches. `main` is reserved for a user-approved integration. Normal integration
and the mandatory post-integration synchronization use `git merge --ff-only`.
The only one-shot alternative is a user-approved `merge-commit` strategy
(`git merge --no-ff`); rebase, reset, force-push, and automatic integration of
another long-lived branch are not managed paths.

The preflight prints the required `code-review` comparison (`main...<source>`).
Run that review with the originating task context and spec, then record either a
completed review or an explicit user-approved skip in the active task record:

```powershell
workspace records note-merge-review <TASK-ID> --status completed --source-branch codex
# or, only after explicit user approval:
workspace records note-merge-review <TASK-ID> --status skipped_user_approved --source-branch codex --reason "<approved reason>"
```

After the approved merge and validation, fast-forward both `codex` and
`claude` to the final `main` tip. If either contains commits not present in the
new mainline, stop for human arbitration; never discard those commits.

- Only path-disjoint changes are `SAFE_TO_CONTINUE` automatically.
- Any shared path, rename/delete interaction, structured configuration, task record, or ledger-entry overlap is `STOP`; preserve the branch and ask the responsible object or workspace owner to arbitrate.
- Never resolve JSON/YAML, manifests, registries, task records, or generated outputs by choosing a side or joining fields. Rebuild generated outputs from accepted sources.
- After a human-resolved merge, run `git diff --check`, the relevant validator, and `workspace workflow check <task-id>`. A failed required check means the merge is not accepted.
- Record non-trivial arbitration and validation evidence in the existing task ledger and task outcome record. To abandon a preflight or failed merge, discard the isolated branch/worktree; the target branch is unchanged.
