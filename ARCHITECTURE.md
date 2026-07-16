# Architecture

## Scope — What This Workspace Exists To Do

This workspace is a governed skill monorepo: it gives many skills one source center, shared infrastructure, validation, reports, and long-term memory without forcing every skill to share the same business logic.

It exists to manage:

- source-of-truth paths and platform projections;
- Git boundary and source/projection separation;
- shared governance protocols;
- validation scripts;
- report snapshots;
- runtime loop records;
- long-term project memory;
- cross-tool conversation continuity across source path migrations;
- related skill packages that benefit from common infrastructure.

It is not intended to make every skill part of one giant agent, nor to force unrelated skills into one shared behavior model.

### Workspace, Package, Skill

```text
workspace
  owns source roots, Git boundary, validation, reports, portability, memory

package or domain
  owns local shared rules for a related group of skills

skill
  owns its runtime behavior and user-facing task contract
```

Current workspace contents are mostly one package in spirit: a character-skill ecosystem around generation, maintenance, runtime diagnosis, and ZYC.

Future unrelated skills can still live in this workspace if they benefit from the same Git boundary, platform projection setup, validation style, and long-term memory layer. They do not have to use every character-specific shared protocol.

### Global Shared vs Domain Shared

Top-level `shared/` should stay focused on workspace-wide rules:

- path governance;
- discovery and failure policy;
- reporting policy;
- protocol validation;
- portability.

Domain-specific shared material should not be forced into top-level `shared/` forever. If future skills form a separate domain, prefer a package/domain-local shared layer, for example:

```text
packages/
  data-tools/
    shared/
    skills/
  browser-tools/
    shared/
    skills/
```

### When A New Skill Belongs Here

A new skill is a good fit for this workspace when most of these are true:

- it should use the same source-of-truth Git repository;
- it benefits from the same projection and validation infrastructure;
- it can follow the same path, report, and failure policies;
- it may share some protocols or runtime-loop conventions;
- it should be maintained by the same long-term project memory.

If only one of these is true, pause before adding it.

### When A New Skill Is A Bad Fit

Give a warning and propose another structure when a new skill:

- has a different privacy boundary;
- needs a different Git lifecycle or release cadence;
- belongs to a separate product or client;
- would make top-level `shared/` absorb unrelated business rules;
- requires platform roots or runtime assumptions that conflict with existing ones;
- would make validation noisy for existing skills;
- cannot safely share the same memory layer.

### Suggested Structures For Misfit Skills

#### Option A: Same Workspace, New Package

Use when the skill shares infrastructure but not business protocols.

```text
packages/<domain-id>/
  shared/
  skills/<skill-id>/
  reports/
```

#### Option B: Same Workspace, Standalone Skill

Use when the skill shares Git/projection/validation infrastructure but has no domain peers yet.

```text
skills/<skill-id>/
```

#### Option C: New Workspace

Use only when the skill or group has a separate Git boundary, privacy boundary, deployment model, or project memory.

### What Not To Overbuild

- Do not create a full new workspace for every unrelated skill. Prefer packages/domains inside the same workspace unless the boundary is truly separate.
- Do not make top-level `shared/` a dumping ground for every domain's business logic.
- Do not require every skill to participate in the character runtime loop.
- Do not invent an "agent profile" unless the project actually becomes an agent runtime. For now, this is a governed skill workspace.

---

## Physical Architecture — Source And Projection Model

`workspace_manifest.yaml -> workspace.source_of_truth` declares the source-of-truth workspace. Git should be operated from that workspace, not from platform projection directories.

`workspace_manifest.yaml -> platform_roots` declares current platform loading roots. `workspace_manifest.yaml -> projections[]` declares the links from those roots back to workspace source folders. Each skill's `exposures[]` selects the projections through which that source is currently discoverable.

Loading surfaces are runtime entry points for tools. They are not independent source repositories.

Agent access is also layered. Skill discovery permits consumption; it does not
grant workspace governance. Codex and Claude Code are default structural
maintainers, while Hermes and OpenCode are bounded record producers. Other
agents may submit requests or receive short-lived external leases without
becoming permanent structural maintainers.

Concrete identity and lifecycle state are registered separately:

```text
shared/agent_registry.yaml       identity, status, host, scope, lifecycle
shared/agent_governance.yaml     roles, capabilities, surfaces, lease policy
workspace_manifest.yaml          platform and Skill exposure facts
scripts/agent_governance.py      validation and effective-access resolution
```

Invalid, incomplete, proposed, suspended, retired, and unknown registrations
resolve to Consumer access. Registration does not authenticate the calling
process; it is a reviewed local contract.

### Skill Contract Dimensions

Each skill is described independently by:

- `role`: responsibility in the ecosystem.
- `authority`: durable effects the skill is permitted to produce.
- `execution_modes`: task-level activation of text output, record writes, or source patches.
- `exposures[]`: platform projections that can discover the skill.

Exposure does not grant authority. Source directory placement describes domain
and lifecycle role, not platform ownership.

### Directory Roles

- `workspace_manifest.yaml`: package, skill, projection, protocol, discovery, failure, and portability registry.
- `shared/`: workspace-global governance protocol layer.
- `shared/agent_registry.yaml`: centralized concrete Agent registration layer.
- `packages/`: related skill families with package-local runtime, engineering, shared, and report layers.
- `packages/character-system/runtime/`: user-facing character skills.
- `packages/character-system/engineering/`: generation, diagnosis, and maintenance skills.
- `packages/character-system/shared/`: character-system protocols, schemas, and templates.
- `skills/`: future standalone skills that share workspace infrastructure but no package domain.
- `reports/`: generated or historical snapshot reports.
- `reports/agent-experiments/`: bounded evidence from testing registrations.
- `packages/character-system/reports/runtime-loop/`: durable runtime drift tracking records and ledgers.
- `scripts/`: validation, bootstrap, reporting, and link-check utilities.
- `PROJECT_CONTEXT/session_migrations.json`: old-to-new source path mappings and external conversation backup evidence.
- `PROJECT_CONTEXT/`: active task memory layer (partitioned task ledger, task records, registry, status, todo, session handoff).
- `WORKSPACE_ENGINEERING/`: reusable AI workspace engineering reference, with Skill Engineering as a subdomain.
- `ARCHITECTURE.md`: this file — workspace scope and physical architecture reference.

### Encapsulation Model

The workspace is not a single agent and does not require every skill to share all business protocols. Treat it as a governed skill monorepo:

```text
workspace -> package/domain -> skill
```

Top-level `shared/` should hold workspace-wide rules. If unrelated skill families are added later, prefer package/domain-local shared layers instead of expanding top-level shared with unrelated business logic.

### Structure Diagram

```text
<workspace.source_of_truth>
|-- workspace_manifest.yaml       machine-readable source of truth
|-- ARCHITECTURE.md               workspace scope and architecture reference
|-- README.md                     entry point and quick-start
|-- shared/                       workspace-global governance
|-- packages/
|   `-- character-system/
|       |-- runtime/
|       |   `-- characters/zyc/
|       |-- engineering/
|       |   |-- generation/character-generator/
|       |   |-- diagnosis/style-doctor/
|       |   `-- maintenance/character-maintainer/
|       |-- shared/
|       `-- reports/runtime-loop/
|-- skills/                       future standalone skills
|-- scripts/                      validation, bootstrap, reports, link checks
|-- WORKSPACE_ENGINEERING/        reusable engineering reference and Skill Engineering subdomain
|-- reports/                      snapshot reports
`-- PROJECT_CONTEXT/              active task memory (ledger, registry, status)

<platform_roots.codex>           Codex Desktop skill loading surface
|-- disk-scan-reporter -> skills/disk-scan-reporter
|-- windows-ai-storage-governor -> skills/windows-ai-storage-governor
|-- character-generator -> packages/character-system/engineering/generation/character-generator
|-- character-maintainer -> packages/character-system/engineering/maintenance/character-maintainer
|-- style-doctor -> packages/character-system/engineering/diagnosis/style-doctor
`-- zyc -> packages/character-system/runtime/characters/zyc

<platform_roots.claude>          Claude Code project skill loading surface
|-- windows-ai-storage-governor -> skills/windows-ai-storage-governor
|-- character-generator -> packages/character-system/engineering/generation/character-generator
|-- character-maintainer -> packages/character-system/engineering/maintenance/character-maintainer
|-- style-doctor -> packages/character-system/engineering/diagnosis/style-doctor
`-- zyc -> packages/character-system/runtime/characters/zyc

<platform_roots.opencode>        OpenCode /skills loading surface
|-- style-doctor -> packages/character-system/engineering/diagnosis/style-doctor
`-- zyc -> packages/character-system/runtime/characters/zyc

<platform_roots.hermes>          Hermes active skill loading surface
|-- style-doctor -> packages/character-system/engineering/diagnosis/style-doctor
`-- zyc -> packages/character-system/runtime/characters/zyc
```

### Skill Responsibilities

- `disk-scan-reporter`: standalone `governance` role with read-only
  `environment_audit` authority. It performs bounded metadata scans and writes
  advisory Markdown and JSON reports; it never performs cleanup or modifies
  scanned content.
- `windows-ai-storage-governor`: standalone `governance` role. It audits,
  classifies, plans, applies user-approved reversible storage changes, and
  verifies Windows AI tool storage without treating platform exposure as
  mutation authority.
- `character-generator`: `production` role with `generator_write` authority. It creates initial style-inspired character skills from authorized corpora and does not maintain mature characters.
- `character-maintainer`: `maintenance` role with `source_patch` authority. It patches and evolves existing character skills without directly editing generator templates from one character patch.
- `style-doctor`: `feedback_diagnosis` role with diagnosis-only authority by default and optional diagnosis record writes. It does not apply patches.
- `zyc`: `runtime_character` role with `runtime_output_only` authority. It may be exposed on compatible platforms without gaining source or ledger write authority.

### Operating Loops

#### Runtime Drift Loop

```text
character runtime failure
-> style-doctor diagnosis
-> handoff packet
-> character-maintainer decision
-> patch note
-> validation note
-> optional generalization note
-> ledger update
```

#### Portability Loop

```text
bootstrap discovery
-> manifest validation
-> migration dry-run
-> protocol validation
-> link check
```

#### Session Continuity Loop

```text
inventory path-indexed sessions
-> create external database/transcript backups
-> export portable sessions when supported
-> record old-to-new path mappings
-> move source
-> audit live sessions and backups
```

Claude Code and OpenCode session data remains under manifest-declared external
data roots. It is not stored inside package or skill source directories.
