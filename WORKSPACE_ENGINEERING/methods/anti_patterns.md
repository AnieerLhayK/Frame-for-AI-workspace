# Anti-Patterns

These are high-risk patterns observed or anticipated from the current workspace work.

## Projection Surface As Source Center

- Anti-pattern: editing a retired or active platform projection root as if it
  were source.
- Why dangerous: changes bypass Git-managed workspace source.
- Observed consequence: source/projection drift becomes hard to diagnose.
- Recommended alternative: edit the manifest-declared source path and check projection links.

## Copied Shared Protocols

- Anti-pattern: copying shared files into skill directories.
- Why dangerous: copies drift independently.
- Observed consequence: validators cannot reliably know which protocol is authoritative.
- Recommended alternative: reference `shared/` and use local docs only for skill-specific interpretation.

## Style Doctor Directly Patches

- Anti-pattern: diagnosis tool mutates character behavior.
- Why dangerous: evidence and decision become entangled.
- Observed consequence: runtime drift cannot be audited cleanly.
- Recommended alternative: output diagnosis and handoff packets for maintainer decision.

## Generator And Maintainer Blurred

- Anti-pattern: every maintainer patch becomes a generator template change.
- Why dangerous: one character's evolution overfits the generator.
- Observed consequence: future generated skills inherit accidental constraints.
- Recommended alternative: use generalization notes and backlog.

## Runtime Drift Without Records

- Anti-pattern: fixing runtime failures without diagnosis, patch, validation, or ledger entries.
- Why dangerous: future sessions cannot reconstruct why behavior changed.
- Observed consequence: repeated drift looks like new drift every time.
- Recommended alternative: use runtime loop records for meaningful failures.

## Reports As Truth Source

- Anti-pattern: treating a generated report as stronger than source files or manifest.
- Why dangerous: reports are stale snapshots.
- Observed consequence: agents may preserve obsolete paths or decisions.
- Recommended alternative: use report headers and defer to source layers.

## Full-Disk Path Search

- Anti-pattern: searching an entire drive to find a workspace.
- Why dangerous: slow, noisy, and may discover the wrong project.
- Observed consequence: path governance becomes nondeterministic.
- Recommended alternative: bounded bootstrap discovery.

## Silent Fallback

- Anti-pattern: using guessed defaults when required files are missing.
- Why dangerous: hides critical drift.
- Observed consequence: scripts appear to pass while using wrong roots.
- Recommended alternative: clear ERROR for required missing, WARNING for optional missing.

## Auto-Generalizing Special Character Experience

- Anti-pattern: treating ZYC-specific evolution as generator truth.
- Why dangerous: character voice lessons may not transfer.
- Observed consequence: generated characters can inherit alien style constraints.
- Recommended alternative: maintainer-reviewed generalization note.

## Absolute Paths Re-Spread Into Skill Docs

- Anti-pattern: adding local machine paths back into skill docs.
- Why dangerous: portability gains disappear.
- Observed consequence: moving workspace requires many manual edits.
- Recommended alternative: centralize local absolute paths in manifest.

## Shared Without Validator

- Anti-pattern: relying only on documents for cross-skill protocols.
- Why dangerous: missing references and files go unnoticed.
- Observed consequence: protocol drift grows gradually.
- Recommended alternative: protocol manifest plus validator.

## Workspace Without Git Baseline

- Anti-pattern: making governance changes before establishing Git state.
- Why dangerous: no clean rollback or review boundary.
- Observed consequence: unrelated changes become hard to separate.
- Recommended alternative: create or confirm baseline before structural edits.

## Automatic Whole-Skill Rewrite

- Anti-pattern: rewriting an entire skill to fix a localized problem.
- Why dangerous: prompt behavior and implicit contracts can be destroyed.
- Observed consequence: tests may pass while voice or workflow changes.
- Recommended alternative: narrow patch with validation note.

---

## Patterns From Experience

### Cross-Project Context Bleed

- Anti-pattern: working on an external project without switching project roots, while the workspace CLAUDE.md and rules remain active.
- Why dangerous: agent may apply workspace governance rules, path policies, and write guards to the wrong repository.
- Observed consequence (2026-06-13): CNN development commits created inside the workspace instead of the CNN repository, requiring replay and project-boundary guard creation.
- Recommended alternative: use explicit project launchers (`claude-project <alias>`) that switch both working directory and project rules. Treat Claude startup CWD as the project selector.

### Platform Exposure Dragged Into Ownership

- Anti-pattern: labeling a skill's platform name as if it defines who owns the skill.
- Why dangerous: same source skill exposed on multiple platforms appears to have multiple owners.
- Observed consequence: early manifest design conflated `platform` (deployment surface) with authority, requiring later decoupling into `exposures[]`.
- Recommended alternative: treat platform exposure as a deployment fact, not an ownership fact. Keep role and authority on the source contract.

### Legacy Compat Fields Left Without Migration Plan

- Anti-pattern: keeping old manifest fields (`platform`, `projection_path`) as silent aliases after their replacement (`exposures[]`) is live.
- Why dangerous: consumers may read the wrong field, and cleanup is delayed until someone audits all consumers.
- Observed consequence: the compatibility period exists with no explicit removal date, risking perpetual tech debt.
- Recommended alternative: set a concrete transition deadline or conditional that fails when the legacy path is the only match.

### Edits Without Task Resolution

- Anti-pattern: starting broad context loading or file modifications before resolving the registered task.
- Why dangerous: loads unnecessary context (token waste), guesses paths, may edit layers the task doesn't own.
- Observed consequence: early governance passes consumed 15k+ tokens on first route before the task registry reduced it to ~5k.
- Recommended alternative: always resolve task first, then load only returned required files. Expand optional context only from evidence.

### Claude Auto Memory As Project State

- Anti-pattern: relying on Claude's conversational memory (`.claude/projects/`) for durable project facts instead of tracked workspace sources.
- Why dangerous: memory data is local, session-scoped, and invisible to other tools.
- Observed consequence: handoff between maintenance agents required explicit
  project context files and handoff packets to maintain continuity.
- Recommended alternative: keep durable decisions in tracked workspace sources (PROJECT_CONTEXT, task ledger, reports). Use auto memory for local convenience only.
