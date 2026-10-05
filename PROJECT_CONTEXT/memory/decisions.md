# Decisions

## muti-ai Uses One Desktop Entry And Independent Real Controls

- decision: Keep source in ai-workbench; expose one muti-ai desktop entry and
  one Qt window with both tool switches visible. Each Controller owns its own
  state, backed by detached local workers. Closing UI preserves operations.
- date: 2026-10-06, accepted implementation plan and theme-settings amendment.
- reason: Make personal local operation usable before installer/public release.
- consequence: Settings select persisted light/dark theme without a shortcut;
  Commander uses @latest. Process state and connection health stay distinct.
  Archive old desktop entries reversibly after verification. Credentials,
  private local config and runtime data are never part of portable projection.
- supersedes: the initial simulation-only presentation below; the first-stage
  record remains historical. Classification UI and public repository are later work.

## ai-workbench Starts With Local Simulation And Explicit Export

- decision: Keep ai-workbench source under packages/ai-workbench, use the existing
  Python 3.13.9 / PySide6 6.9.2 runtime and one Qt window with independent
  simulated Commander/Hermes pages. Keep its maintenance skill development-only
  and unexposed. Workspace remains authoritative.
- reason: Verify personal local usability and lifecycle interaction before real
  service control, installers or public distribution.
- date if known: 2026-10-05, user-approved first-stage implementation plan.
- consequence: Use explicit portable export files and a local staging preview;
  exclude this package precisely from Frame. Real adapters, authorization,
  desktop replacements, repository identity and licensing need later decisions.

## Sci-system expands by evidence-bearing stages

Sci-system begins with a package-local scientific presentation contract and one
unexposed development skill, project-showcase-pack. The user owns and
authorized its import from the configured research source; it is adapted for
scientific evidence state and output safety, but has no workspace projection.
Its authorized capability sequence is presentation and reporting, controlled
provenance and intake, processing and analysis, then reproducible automation
and visualization. A later stage requires an explicit design, task record,
fixtures, and authority decision; the current package does not authorize
research-data mutation, network access, or publication.

## Showcase-Packer is a clean-room native skill

The unversioned, unlicensed research source `project-showcase-pack` is design
inspiration only and is neither migrated nor copied. `skills/content/showcase-packer/`
is independently authored, with a user-confirmed preview-before-build gate and
default exclusion of high-risk material. Its derived output is confined to the
manifest-declared workspace output root and never changes source material.

## Manifest-Declared Workspace Is The Only Source Center

- decision: Treat `workspace_manifest.yaml -> workspace.source_of_truth` as the only source-of-truth workspace.
- reason: Prevent drift between platform projections and editable source.
- date if known: 2026-05-27 baseline governance.
- consequence: Git operations and source edits belong in the manifest-declared workspace root.

## Platform Directories Are Projection Surfaces

- decision: Platform directories declared by `workspace_manifest.yaml -> platform_roots` and `projections[]` are runtime projection surfaces.
- reason: Codex and OpenCode need platform entry points, but those paths should not become independent source roots.
- date if known: 2026-05-27 Git governance.
- consequence: Do not commit or maintain source from platform directories.

## Exposure Does Not Define Role Or Authority

- decision: Separate each skill's role, durable authority, execution mode, and platform exposure.
- reason: A skill may be useful on multiple platforms without changing what it is allowed to do.
- date if known: 2026-06-09 architecture compatibility phase.
- consequence: Agents and scripts must not infer ownership or write permission from the invoking platform or exposure path.

## Legacy Platform Fields Remain Compatibility Aliases

- decision: Keep `skills[].platform` and `skills[].projection_path` temporarily as aliases for the first `exposures[]` entry.
- reason: Existing scripts and external consumers may still depend on the old single-platform shape.
- date if known: 2026-06-09 architecture compatibility phase.
- consequence: New logic uses `exposures[]`; validators ensure legacy aliases stay synchronized until retirement.

## Shared Is Single-Source

- decision: `shared/` is a single protocol source, projected to platforms when needed.
- reason: Copying shared protocols into skills creates protocol drift.
- date if known: manifest established before current governance series.
- consequence: Skills reference shared protocols instead of embedding copies.

## Reports Are Snapshots

- decision: Reports summarize observations and are not source-of-truth documents.
- reason: Reports can become stale after manifest, shared policy, Git, or projection changes.
- date if known: 2026-05-27 report drift governance.
- consequence: If a report conflicts with manifest/shared/current Git, trust the source and regenerate the report.

## Manifest Is Machine-Readable Source Of Truth

- decision: `workspace_manifest.yaml` owns roots, skills, projections, protocols, discovery, failure policy, and portability metadata.
- reason: Centralized registry is safer than scattered path assumptions.
- date if known: manifest exists as workspace source before this context layer.
- consequence: Scripts should read the manifest rather than duplicate path arrays.

## Generator Does Not Maintain Mature Characters

- decision: `character-generator` creates initial scaffolds and generation workflow assets.
- reason: Mature characters accumulate manual evolution that generation templates should not overwrite.
- date if known: reinforced during report drift and runtime loop governance.
- consequence: Existing character repairs go to `character-maintainer`.

## Maintainer Does Not Directly Modify Generator

- decision: `character-maintainer` may record generalization notes but should not directly edit generator templates from one character patch.
- reason: Character-specific fixes can damage future generated characters if promoted too early.
- date if known: runtime loop governance.
- consequence: Generator changes require reviewed generalization evidence.

## Style-Doctor Does Not Apply Patches

- decision: `style-doctor` diagnoses runtime drift and creates diagnosis/handoff records.
- reason: Diagnosis and maintenance are separate responsibilities.
- date if known: runtime loop governance.
- consequence: Patches are accepted/rejected/deferred by `character-maintainer`.

## ZYC Experience Is Not Automatically Generalized

- decision: ZYC-specific runtime lessons default to character-specific.
- reason: ZYC is a mature manually evolved character with special style constraints.
- date if known: runtime loop governance.
- consequence: Generator promotion requires a maintainer-approved generalization note.

## Git Tracks Workspace, Not Platform Roots

- decision: Git baseline belongs to the manifest-declared workspace root; platform `.git` metadata is not primary.
- reason: Avoid competing histories and source confusion.
- date if known: 2026-05-27 Git governance.
- consequence: No live `.git.disabled-*` projection metadata remains. Historical
  reports may retain the old name, but registered publishers and manifest
  projections define current Git boundaries.

## Package Protocols And Asset Catalogs Have Separate Ownership

- decision: Validate each package's protocol manifest against a generic protocol schema and a declared domain profile; keep package-owned skills/tools in its separate package catalog.
- reason: Protocol consumers should not have to interpret asset inventory fields, while package owners still need auditable lifecycle state.
- date if known: 2026-09-25 Workspace skill taxonomy migration, superseding the 2026-08-30 combined inventory decision.
- consequence: `protocol_manifest.json` contains protocol data only; `package_manifest.json` owns package skill/tool inventory and registration status.

## Skill Registration Is Owned By Local Catalogs

- decision: Keep only catalog roots and package declarations in the root manifest; store standalone registrations in category registries and package-owned skill/tool records in each package's `package_manifest.json`. A single loader aggregates registered skills into the runtime `skills[]` view.
- reason: The root manifest had become a coordination bottleneck. Local ownership lowers contention while preserving one compatibility contract for runtime consumers and keeping package protocols focused on protocols.
- date if known: 2026-09-25 Workspace skill taxonomy migration.
- consequence: New consumers must use `scripts.workspace.manifest_loader`; do not scan catalog directories or restore per-skill root registrations. Category changes require a planned path/reference migration and an effective-registration parity check.

## Runtime-Loop History Is Audited Read-Only

- decision: Validate runtime-loop IDs, links, ledgers, states, and evidence but
  never auto-repair historical packets or ledgers.
- reason: Historical audit records must remain reviewable and must not be
  silently rewritten by a health check.
- date if known: 2026-08-30 workspace optimization batch 2.
- consequence: malformed, duplicate, broken, or inconsistent records are
  errors; unledgered history is a warning and strict mode exits 2.

## Task Routing Stays Declarative

- decision: Keep task routing in the task registry and resolve only registered
  context, scope, validation, and tool policy. Do not maintain a second prompt
  registry or inject task-specific prompt frames. Put durable behavior in the
  owning `packages/` or `skills/` instructions; keep `USAGE_GUIDES/` for platform
  loading, workspace CLI onboarding, and the three published template guides.
- reason: The prompt registry duplicated task and skill guidance, expanded the
  resolver/CLI surface, and created another path inventory to maintain.
- date if known: 2026-09-27 USAGE_GUIDES simplification.
- consequence: Retire prompt list/show and prompt-token reporting. The former
  knowledge lookup recommendation was superseded on 2026-09-29; use
  `workspace task list`, then resolve one exact task id.

## Full-Drive Discovery Is Forbidden

- decision: Bootstrap discovery is bounded upward from a known start path.
- reason: Full-drive scans are slow, unsafe, and can bind the project to unrelated folders.
- date if known: manifest portability/bootstrap discovery phase.
- consequence: Use `scripts/workspace/bootstrap_workspace.py` and manifest discovery policy.

## Agent Review Must Stay Independent

- decision: User judgment decides subjective style fit, but agent review must independently flag engineering and safety risk.
- reason: A character output can feel appealing while still drifting facts, overfitting motifs, weakening privacy boundaries, or generalizing a character-specific trick too early.
- date if known: 2026-06-04 ZYC validation case review.
- consequence: Validation notes should separate user aesthetic judgment from agent checks and record disagreement when needed.

## Script Implementations Live In Responsibility Packages

- decision: Keep script implementations in responsibility packages under
  `scripts/workspace/`, `scripts/validation/`, `scripts/publishing/`,
  `scripts/platform/`, and `scripts/reporting/`.
- reason: The root scripts directory had high coupling and repeated path and
  subprocess setup, while existing callers depend on legacy command and import
  paths.
- date if known: 2026-07-16 scripts governance migration.
- superseded: The root compatibility adapters were retired on 2026-07-27 by
  commit `3527b27`; no legacy root command or import adapter is maintained.
- consequence: Internal code imports package implementations and shared runtime
  helpers. `scripts/` remains a Python package marker, and tests mirror package
  domains under `scripts/tests/`.

## README Layers Are Navigation, Not Parallel Authority

- decision: Keep root README and section READMEs as concise navigation and
  contracts, while placing volatile facts in the manifest, shared policy, live
  status, or generated reports that own them.
- reason: Repeating paths, platform details, and maintenance procedures across
  bilingual READMEs causes drift and consumes startup context.
- date if known: 2026-07-16 README governance pass.
- consequence: Existing `README.zh-CN.md` companions are synchronized
  semantically; missing companions remain documented exceptions rather than
  automatic new files. Platform projections are not edited as source.

## Public Projection README Content Follows Publisher Boundaries

- decision: Map README facts to public repositories only through the registered
  publisher for that repository.
- reason: Frame and Chatty Ch System expose different
  source surfaces and must not become copies of the private workspace.
- date if known: 2026-07-16 README governance pass.
- consequence: Generated public README templates and package-facing README
  content stay aligned with their publisher; root workspace documentation is
  not copied wholesale into every remote.

## PLAN Records Do Not Authorize Execution

- decision: Keep local PLAN records beside task outcome records as optional prospective-work coordination; PLANs never grant authority and may link to a TASK only when execution starts.
- reason: Open work can outlive a Git baseline and must not silently gain workspace or external write authority.
- date if known: 2026-09-01 local tracker migration; persistence scope reviewed 2026-09-30.
- consequence: PLAN mutation and execution each require their own active TASK record; claims only coordinate ownership and expire after 24 hours. Cross-session MAP persistence is retired; Wayfinder is conversation-only.

## Remote-Only Repositories Use A Separate Registry And Explicit Retirement Gate

- decision: Record remote-only repositories separately from local project and
  launcher registries; expose their retirement workflow only to Codex through
  explicit `$kill-for-remote` invocation.
- reason: A nonexistent checkout cannot be a launch root, and deleting an
  external source tree needs stronger identity, confirmation, and audit gates
  than ordinary workspace maintenance.
- date if known: 2026-09-03 remote-only repository workflow.
- consequence: `pending_retirement` remains non-authorizing; an approved
  `cleanup_migration` run must pass a fresh GitHub audit and exact ID/path
  confirmation before the checkout is sent to the Windows Recycle Bin.

## Shared Development And Standing Delivery Authority

- decision: All agents develop concurrently on dev, including coordinated same-file edits; complete validated and reviewed batches fast-forward to main. Ordinary commits, dev/main pushes and registered publication have standing user authorization.
- reason: Agent-specific branches imposed synchronization overhead without matching task boundaries. Shared development retains parallel editing; sessions coordinate overlapping work and serialize Git mutations.
- date if known: 2026-09-08, explicitly confirmed by the user.
- consequence: Preserve capability scopes; stop on unfinished batches, stale evidence, divergence, conflicts or failed delivery. Retire codex/claude refs only after ancestry and worktree checks.

## Branches And Worktrees Are Reused By Default

- decision: Workspace-managed repository work starts from its configured collaboration branch and reuses a suitable existing worktree. New worktrees require a mandatory isolation workflow, an unavailable safe checkout for the required operation, a workspace that cannot safely contain the work after coordination, or an explicit user request. A worktree need does not itself authorize a new branch; branch creation is justified separately by the user, target repository rules, or a workflow requiring an independent commit line.
- reason: Per-task branches and checkouts add maintenance and coordination cost. Reuse keeps ordinary work on established collaboration lines while preserving isolation for workflows that require it.
- date if known: 2026-09-23, user-confirmed Git workflow rule.
- consequence: Reuse a suitable main checkout for integration; create one only when unavailable and keep using it. Target repository instructions take precedence over this Workspace default. Record the reason for each newly created branch or worktree.

## Claude LiteLLM Routes Are Locally Managed

- decision: Manage Claude Code-facing LiteLLM routes through the local interactive route manager; retain provider credentials only in Claude `settings.json -> env` and reference them from LiteLLM YAML as `os.environ/<VARIABLE>`.
- reason: A logical route decouples Claude Code selection from provider model IDs, while centralizing credential handling, backups, compatibility slots, and rollback.
- date if known: 2026-09-13 Claude LiteLLM V4.1 Flash migration.
- consequence: Add, update, remove, or reassign routes through `Configure-ClaudeLiteLLM.ps1`; do not place a literal provider credential in `litellm-config.yaml`.

## DeepSeek Harness Uses A Two-Phase, Default-Deny Promotion Path

- decision: Keep DeepSeek Harness registered as `record_producer`; permit only
  a separately leased, at-most-24-hour `structural_write` pilot in an isolated
  worktree, protected by the local Cordis governance adapter.
- reason: Structural capability needs runtime enforcement, a narrow scope, and
  verifiable evidence; prompts, dynamic plugins, and broad tool permissions are
  not a security boundary.
- date if known: 2026-09-15 controlled-pilot implementation.
- consequence: Pin DSH and adapter versions, use local JSONL only, deny web,
  MCP, dynamic Cordis, subagents, remote Git, credential tools, and telemetry
  export. A separate reviewed TASK is required for permanent promotion.

## Codex Owns Core Governance; Claude Retains Development Delivery

- decision: Codex owns core governance. Claude is a development maintainer and can independently deliver ordinary batches. A mixed governance batch requires Codex or explicit user approval bound to source and target commits; approval permits integration and registered publication, not governance editing. Claude is no longer a structural reviewer or lease issuer.
- reason: Preserve ordinary development autonomy while removing equal governance authority. One shared authorization interface keeps runtime, workflow and delivery decisions consistent.
- date if known: 2026-10-02, user-confirmed specification PLAN-20261002-001.
- consequence: Protect core controls before ordinary path rules; deny unclassified writes; retain owned TASK and whole-batch checks. Retire both project CLAUDE.md imports only after npm upgrade and fresh root/nested AGENTS.md loading verification. This is cooperative workflow enforcement, not hostile-process isolation.

## Chatty Owns Corpus Preparation And Its Portable Public Toolchain

- decision: Include the QQ raw material filter in Chatty Ch System. Keep portable
  generation, content contract, checker, documentation, CI and tests in
  character-system/distribution/public-projection. Workspace remains the sole
  owner of host paths, remote registration, TASK authorization and synchronization.
- reason: Corpus preparation is a stage of the same character engineering system;
  separate public publishers duplicated maintenance without independent source ownership.
- date if known: 2026-10-05, user-confirmed and implementation-authorized plan.
- consequence: Preserve filter package and CLI identities and local data defaults
  through host configuration. Review and convert JSONL before generator handoff.
  Retire the separate filter publisher and annotate/archive its remote after Chatty
  validation, preserving all history, branches and contributions; do not delete it.
  Bilingual documentation incorporates useful ideas from both unmerged README PRs
  with attribution, without making remote changes authoritative.
