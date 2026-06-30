# Branch Merge Review

Use this prompt before merging a workspace maintenance branch into `main`.

```text
Task:
Review whether this branch is ready to merge into `main`:
<branch name>

Start:
1. Run `git status --short --branch --untracked-files=all`.
2. Run `git log --oneline --decorate --left-right --cherry-pick main...HEAD`.
3. Run `git diff --name-status main...HEAD`.
4. Identify the task ids and validation commands represented by the branch.

Guardrails:
- Do not merge until the user explicitly approves.
- Do not delete the branch until the merge is complete and the worktree is clean.
- Prefer fast-forward merge when the branch is linearly ahead of `main`.
- If the branch and `main` both changed task ledger, todo, or usage guides,
  inspect those files before merging.
- Do not push unless explicitly asked.

Expected output:
- Branch relationship to `main`.
- Commit list.
- Risky files or likely conflicts.
- Validation already run and validation still needed.
- Recommended merge, rebase, or hold decision.
```
