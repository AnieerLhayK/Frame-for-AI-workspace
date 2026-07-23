# Workspace Engineering Knowledge Base

`WORKSPACE_ENGINEERING/` is the reusable engineering knowledge layer for
designing, operating, evolving, and sharing AI workspaces.

It covers more than Skill construction:

- workspace and repository architecture;
- Agent identity, registration, authority, and lifecycle;
- source, projection, data, cache, Session, and output boundaries;
- task routing, context budgets, and developer interfaces;
- governance, validation, reporting, portability, and release practices;
- Skill Engineering as one specialized subdomain.

This layer is a reference book built from reviewed experience. It is not the
current workspace status, an enforceable policy, a raw link collection, or a
claim that every pattern is universally correct.

## Relationship To Other Layers

- `PROJECT_CONTEXT/`: current workspace state, active memory, tasks, and handoff.
- `shared/`: enforceable contracts for this workspace.
- `workspace_manifest.yaml`: machine-readable current workspace facts.
- `reports/`: generated or authored snapshots.
- `WORKSPACE_ENGINEERING/`: reusable methodology and evidence-backed lessons.

When these layers disagree about current behavior, the knowledge base does not
override Manifest, policy, source, or current Git state.

## Book Structure

### Workspace Engineering

- `philosophy.md`: general engineering posture.
- `architecture_patterns.md`: reusable system structures.
- `workspace_patterns.md`: repository and workspace organization.
- `governance_patterns.md`: authority, validation, and continuity.
- `context_structure_refactoring.md`: reusable deep-module and path-migration method.
- `portability_patterns.md`: movement and machine-boundary lessons.
- `anti_patterns.md`: recurring failure modes.
- `knowledge_provenance.md`: intake and attribution rules.

### External Knowledge

`external_knowledge/` contains bounded evaluations of adding external
knowledge retrieval (RAG, knowledge base, note system) without
implementing or deploying anything.

- `external_rag_planning.md`: staged evaluation and tool comparison.

### Skill Engineering

`skill_engineering/` contains reusable Skill-specific methods:

- Skill design;
- prompt engineering;
- runtime loops;
- drift and style alignment;
- validated evolution patterns.

### Evidence

- `case_studies/`: real incidents and completed changes.
- `experiments/`: bounded hypotheses and results; currently dormant until a
  real experiment is opened.
- `templates/`: reusable authoring structures.
- `reports/`: snapshots about this knowledge layer.

## When To Add Knowledge

Add an entry only when a completed task produces at least one of:

1. A reusable pattern or decision framework.
2. A recurring anti-pattern.
3. A real incident or migration case.
4. A validated or refuted experiment.
5. A material change in long-term risk or architecture.

Ordinary task status stays in `PROJECT_CONTEXT/tasks/ledger/`.

## Completion Writeback Check

At the end of a workspace maintenance task, the agent should make a short
knowledge writeback decision:

- **Write back** when the task produced a reusable method, anti-pattern,
  incident, migration lesson, experiment result, or architecture tradeoff.
- **Record no writeback** when the task only changed local state, applied an
  existing rule, refreshed reports, or fixed a narrow defect without a reusable
  lesson.

Use the smallest durable home. Add operational continuity to
`PROJECT_CONTEXT/tasks/ledger/`, reusable methodology to this directory, and
enforceable rules to `shared/` only when a policy contract actually changes.

## Evidence Levels

Each new lesson should make its evidence level clear:

- **Observed**: seen in a real environment but not yet reproduced.
- **Validated locally**: tested in this workspace or another controlled project.
- **Repeated**: confirmed across more than one task or environment.
- **External reference**: adapted from an attributed source and not yet fully
  validated locally.
- **Retired**: preserved for history but no longer recommended.

## Sharing Principle

Write so another AI engineer can understand the context, tradeoffs, failure
modes, and verification steps without needing this machine's private data.
Remove secrets, private corpus material, local identity details, and volatile
absolute paths from shareable guidance.

External ideas may be incorporated only through
`knowledge_provenance.md`. Summarize and transform them into locally reviewed
engineering knowledge; do not copy substantial third-party material or erase
its origin.
