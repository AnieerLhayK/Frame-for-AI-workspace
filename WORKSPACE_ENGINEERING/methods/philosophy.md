# Engineering Philosophy

These principles are experience-based. They guide future skill engineering, but they can be revised when better evidence appears.

## Generator Is Not Maintainer

- Principle: a generator creates initial skill structure; a maintainer evolves existing skills.
- Reason: creation and evolution have different risk profiles.
- Consequences: generator templates should not absorb every character-specific fix; maintainers should patch narrow existing behavior.
- Known tradeoffs: separation creates extra handoff work, but reduces broad template drift.

## Style Doctor Is Not Patch Applier

- Principle: diagnosis and mutation should stay separate.
- Reason: style diagnosis benefits from being conservative and evidence-focused.
- Consequences: style-doctor outputs diagnosis and handoff packets; character-maintainer decides and patches.
- Known tradeoffs: slower than direct patching, but more auditable.

## Projection Surface Is Not Source Of Truth

- Principle: platform skill directories are runtime entry points, not source roots.
- Reason: editing projections creates divergence from Git-managed source.
- Consequences: source files live under the workspace root; projection links should be checked, not hand-maintained.
- Known tradeoffs: platform debugging sometimes tempts direct edits.

## Reports Are Not Truth Sources

- Principle: reports are snapshots.
- Reason: reports can become stale immediately after code or manifest changes.
- Consequences: reports need headers and must defer to manifest, shared protocols, source files, and Git state.
- Known tradeoffs: snapshots are still useful for audit trails.

## Shared Should Be Unified, Not Copied

- Principle: shared protocols should stay single-source.
- Reason: copied protocols drift silently.
- Consequences: skills reference shared protocols instead of maintaining local clones.
- Known tradeoffs: domain-specific rules may need package-local shared layers instead of top-level `shared/`.

## Runtime Drift Should Be Traceable

- Principle: runtime failures should leave durable records.
- Reason: otherwise fixes cannot be reviewed, reverted, or generalized responsibly.
- Consequences: diagnosis, handoff, patch, validation, and generalization notes are separate artifacts.
- Known tradeoffs: record keeping adds friction to tiny fixes.

## Evolution Should Be Auditable

- Principle: every meaningful behavior change should have an explanation trail.
- Reason: skill behavior is easy to alter accidentally.
- Consequences: ledgers and validation notes matter as much as the patch.
- Known tradeoffs: some experiments remain informal until they become recurring.

## Portability Beats "It Runs Here"

- Principle: a workspace should explain how to recover after path changes.
- Reason: hardcoded local paths are fragile.
- Consequences: manifest portability, bootstrap discovery, and migration dry-run are first-class maintenance concerns.
- Known tradeoffs: portability work can feel abstract until a migration happens.

## Validators Beat Pure Documentation Governance

- Principle: documents should be backed by checks where feasible.
- Reason: humans forget cross-file contracts.
- Consequences: protocol manifests and validators catch missing files and references.
- Known tradeoffs: validators should stay lightweight enough to avoid false-positive fatigue.

## Bounded Discovery Beats Full-Disk Search

- Principle: discovery should walk known parents with a limit.
- Reason: full-drive search is slow, unsafe, and can find the wrong project.
- Consequences: bootstrap scripts use max parent depth and clear errors.
- Known tradeoffs: unusual launches may need explicit start paths.

## No Silent Fallback

- Principle: when a required source is missing, fail loudly.
- Reason: silent fallback hides drift.
- Consequences: scripts distinguish required errors from optional warnings.
- Known tradeoffs: strict failure interrupts work earlier.

## Do Not Invent Paths

- Principle: tools should not fabricate plausible source or projection paths.
- Reason: invented paths corrupt governance.
- Consequences: scripts read manifest data and report what they tried.
- Known tradeoffs: users may need to update the manifest.

## Do Not Auto-Generalize Character Evolution

- Principle: one character's fix is not automatically generator wisdom.
- Reason: character-specific voice and history can be overfit.
- Consequences: generalization notes require a maintainer decision.
- Known tradeoffs: some broadly useful lessons wait in backlog longer.

## Small Patch Beats Big Rewrite

- Principle: prefer the smallest change that preserves behavior and improves the target issue.
- Reason: skills often encode subtle prompt and style contracts.
- Consequences: maintainers should avoid broad rewrites unless the owner asks for them.
- Known tradeoffs: small patches may leave deeper redesign for later.

