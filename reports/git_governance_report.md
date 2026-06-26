---
report_name: git_governance_report
generated_at: 2026-05-27 12:43:57 +08:00
generated_by: manual git governance pass
source_root: ${WORKSPACE_ROOT}
manifest_path: ${WORKSPACE_ROOT}\workspace_manifest.yaml
manifest_version: 1.0.0
manifest_last_modified: 2026-05-26 22:36:48 +08:00
source_commit: 7099172
report_scope: Git boundary stabilization and baseline establishment
report_is_snapshot: true
truth_source:
  - workspace_manifest.yaml
  - shared/
  - current git commit
staleness_policy: Regenerate or supersede after Git boundary, baseline, or source-of-truth changes.
---

Report is a snapshot. Manifest is the source of truth. If this report conflicts with the manifest, trust the manifest and regenerate or supersede the report.

# Git Governance Report

Generated: 2026-05-27 12:43:57 +08:00

## Scope

This report covers Git governance stabilization only. No workspace migration, skill logic changes, shared protocol changes, manifest changes, junction rebuilds, file deletion, or private corpus cleanup were performed.

## Source Of Truth

- Primary source repository: `${WORKSPACE_ROOT}`
- Codex projection surface: `D:\skills_codex`
- OpenCode projection surface: `D:\opencode\.opencode\skills`
- Compatibility entry point: `D:\AgentWorkspace`

`${WORKSPACE_ROOT}` is the only primary source repository for this workspace.

## Pre-Operation Git Status

`${WORKSPACE_ROOT}` had a `.git` directory but no commits:

```text
## No commits yet on main
?? .gitignore
?? codex/
?? opencode/
?? reports/
?? scripts/
?? shared/
?? workspace_manifest.yaml
```

`D:\opencode\.opencode\skills` had an independent `.git` repository, but it was a projection surface under the current architecture. Its status showed old `character/ZYC/...` paths as deleted and current projection directories as untracked.

`D:\AgentWorkspace` had an independent `.git` repository. It was not modified.

`D:\skills_codex` did not have a `.git` repository.

## `.gitignore` Governance

The workspace `.gitignore` already excluded:

- `__pycache__/`
- `*.pyc`
- `.cache/`
- `tmp/`
- `.env`
- `*.log`
- `*.lnk`
- `dist/`
- `*.zip`
- `corpus/`
- `reports/legacy_git_metadata/`

Added in this pass:

- `**/reports/corpus_stats.md`

Reason: corpus statistics are generated artifacts and may contain corpus-derived metadata. They should not be part of the baseline repository.

## Sensitive And Generated Files Excluded

Confirmed ignored:

- `opencode/characters/zyc/霁梦(1).docx.lnk`
- `opencode/characters/zyc/dist/zyc-writing-style.zip`
- `codex/character-generator/corpus/writerA/sample.md`
- `opencode/characters/zyc/reports/corpus_stats.md`
- Python `__pycache__/` and `*.pyc`
- `reports/legacy_git_metadata/`
- generated `codex/character-generator/characters/writerA/`

The staged baseline was checked for these patterns before commit:

```text
*.lnk
*.zip
*.pyc
.env
*.log
corpus/
dist/
__pycache__/
.cache/
tmp/
legacy_git_metadata/
reports/corpus_stats.md
```

No matching sensitive or generated paths were staged.

## Junction And Symlink Review

No reparse points were found inside `${WORKSPACE_ROOT}`, so the primary workspace repository will not recursively commit platform junction targets as ordinary directories.

Projection surfaces remain junction-based:

- `D:\skills_codex\character-generator` -> `${WORKSPACE_ROOT}\codex\character-generator`
- `D:\skills_codex\character-maintainer` -> `${WORKSPACE_ROOT}\codex\character-maintainer`
- `D:\skills_codex\shared` -> `${WORKSPACE_ROOT}\shared`
- `D:\opencode\.opencode\skills\zyc` -> `${WORKSPACE_ROOT}\opencode\characters\zyc`
- `D:\opencode\.opencode\skills\style-doctor` -> `${WORKSPACE_ROOT}\opencode\style-doctor`
- `D:\opencode\.opencode\skills\shared` -> `${WORKSPACE_ROOT}\shared`

These projection surfaces are not nested inside `${WORKSPACE_ROOT}`, so the primary repository does not absorb them.

## Baseline Commit

Created baseline commit:

```text
64f31ecf4c414182d07802829fcca847bc93c302
```

Commit message:

```text
chore: establish workspace git baseline
```

The baseline commit contains source files, manifest/reporting infrastructure, and safe workspace reports. It excludes private corpus, shortcuts, archives, caches, generated character output, and legacy Git metadata.

## Projection Surface `.git` Handling

`D:\opencode\.opencode\skills\.git` was confirmed to belong to a projection surface rather than the primary source repository. It was not deleted.

It was safely renamed to:

```text
D:\opencode\.opencode\skills\.git.disabled-20260527-124357
```

This prevents accidental use of the projection surface as a competing source repository while preserving the old Git metadata for manual inspection or recovery.

## AgentWorkspace `.git`

`D:\AgentWorkspace\.git` exists.

Action taken:

- none

Recommendation:

- Treat it as non-primary until manually reviewed.
- Do not use it as the source-of-truth repository for skills.
- Do not delete or rename it without a separate governance decision.

## Current Repository State

After the baseline commit, `${WORKSPACE_ROOT}` has no unstaged or staged source changes. Ignored generated/private paths remain visible under `git status --ignored`, as expected.

## Follow-Up Recommendations

1. Keep `${WORKSPACE_ROOT}` as the only primary source repository.
2. Do not run commits from `D:\skills_codex` or `D:\opencode\.opencode\skills`.
3. Leave `D:\opencode\.opencode\skills\.git.disabled-*` in place until manually archived outside the projection surface.
4. Review `D:\AgentWorkspace\.git` separately before deciding whether it should also be disabled.
5. Consider adding a workspace-level `.gitattributes` in a future Git-only pass if CRLF warnings become noisy.
