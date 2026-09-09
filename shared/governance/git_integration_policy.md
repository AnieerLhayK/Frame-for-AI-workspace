# Shared Development And Stable Integration

`git_branch_governance` in `agent_governance.yaml` owns branch names and delivery
authority. Every agent develops on `dev`; `main` contains accepted stable batches.
Agent capabilities and path scopes still apply.

## Concurrent development

Each session starts its own TASK with `workspace_write`, `--owner-agent <agent>`
and `--owner-session <session-id>`. Multiple sessions may hold write authority
and edit the same file; they coordinate directly without exclusive writer or
file ownership locks. Preserve other sessions' edits. Never stage the whole
workspace blindly: inspect and stage only the intended task changes, using
hunks when a file contains another session's work.

Coordinate Git staging, commits, integration and pushes serially. Recheck the
index, working tree and tips when taking over a Git operation. An active TASK
is attribution, not proof of process identity. Other active development TASK owners must confirm their batch is complete
before integration; record each confirmation with `--ready-task <TASK-ID>` on
the batch review note. Missing confirmations stop integration, not editing.
Confirm a session stopped before cancelling abandoned records.

Use the shared workspace on `dev`. Do not switch branches or rewrite history
there. Integrate `main` in an isolated worktree. The initial migration has one
user-authorized exception: with other writers stopped and a clean tree, create
`dev` from verified `main` and switch the existing workspace once. Preserve owned
migration edits through a named stash and restore them afterwards.

## Automatic delivery

The user grants standing authority for ordinary commits, reviewed fast-forward
integration, ordinary pushes of `dev`/`main`, and registered publication. This
replaces per-delivery approval; it does not authorize unrelated deletion,
history rewriting, arbitrary remote targets, or bypassing capabilities.

1. At each task boundary inspect the whole `main...dev` batch. Commit complete
   work belonging to the task. Unfinished work holds the entire batch; do not
   cherry-pick around it.
2. Run affected routed validators, `git diff --check`, and `workspace workflow
   check <task-id> --record-id <TASK-ID> --include-committed`. This checks cumulative
   fast-forward commits and current edits against task scope. When concurrent
   TASKs contribute commits, repeat `--batch-task <TASK-ID>` to run an explicit
   aggregate check from their common baseline. Each additional path must match
   a participating TASK scope and its recorded agent capability; the output
   identifies covering TASKs. This read-only batch check does not expand any
   session's individual write authority. For coordinated
   edits to files already dirty when the TASK started, repeat the exact
   `--coordinated-path <file>`; path and capability checks still apply. Review the complete batch with
   `code-review main`. Resolve actionable findings before continuing.
3. On the reviewed source commit record completed review with `workspace records
   note-merge-review <TASK-ID> --status completed --source-branch dev
   --validation-command "<passed command>"` (repeat commands as needed). Commit
   only that TASK record as a receipt. Preflight checks source/target hashes and
   permits exactly one receipt-only successor that appends this note without
   changing any other field or file. Any other successor or changed target needs
   fresh validation and review. Historical skips cannot authorize integration.
4. Run `workspace merge main --head dev --agent <agent> --record-id <TASK-ID>`.
   This is read-only. With clean trees and successful preflight, recheck both
   tips and run `git merge --ff-only dev` in the main integration worktree.
   Coordinate with other sessions throughout integration.
5. Fetch and compare remote tips before ordinary pushes. Remote main must match
   the reviewed target or already equal the delivered source; remote dev must
   be its ancestor. Stop on divergence or push rejection; never force-push.
   Push dev/main, then invoke the registered aggregate publisher with the active
   TASK's `external_write` authority and existing capability/path checks.
6. Record delivery and finalize the TASK after validation and publication. Commit
   its final TASK, linked completed PLAN and day-ledger changes as an audit batch.
   Review that batch against main, validate records/plans and diff, then append a
   completed review with `--audit-close` and commit its single receipt. Preflight
   accepts this successfully finalized TASK only for those exact audit paths.
   Integrate and push this reviewed audit batch without a new TASK or another
   finalization. Audit-only closure does not change published source and does
   not trigger another publication. This is the terminal delivery step.
   A completed audit-close receipt already present on main blocks another
   closure for the same TASK. Undelivered stale receipts may be renewed.

A failed check, unresolved finding, dirty tree, divergence or conflict stops
integration. Preserve commits for human arbitration. Publication failure stops
delivery without resetting accepted history. Main audit paths retain their
limited existing exception; ordinary source writes on main remain denied.

## Retiring agent branches

After dev/main delivery, fetch the exact old codex/claude refs. Verify each local
and remote tip is an ancestor of delivered main and no worktree occupies a
retiring branch. Delete only those named local and remote branches using ordinary
Git operations; recheck remote tips immediately before deletion. Unique commits,
changed remote tips or worktree occupancy stop retirement. Do not recreate agent
branches or synchronize them after delivery.
