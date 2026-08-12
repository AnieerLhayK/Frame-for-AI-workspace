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

The directory uses broad lifecycle buckets rather than one directory for
every kind of experience. Fine-grained types and evidence levels belong in
the document and knowledge indexes, not in a growing directory tree.

### Methods

- `methods/`: reusable methods, patterns, anti-patterns, and guidance.
- `methods/skill_engineering/`: the Skill-specific methods subdomain.

The current method files cover general posture, architecture, workspace
organization, governance, migration, portability, anti-patterns, and
knowledge provenance.

### Proposals

`proposals/` contains bounded plans and evaluations that have not yet become
stable reusable methods.

- `proposals/external_rag_planning.md`: staged evaluation and tool comparison.
- `proposals/public-repo-plan.md`: public repository publication plan.

### Evidence

`evidence/` contains observed or validated experience, including case studies,
experiments, retrospectives, and reports. New evidence does not require a new
top-level directory for each subtype.

- `evidence/agent_registration_contract.md`: validated registration case study.
- `evidence/skill_engineering_setup_report.md`: historical setup snapshot.

### Templates

`templates/` contains reusable authoring structures. Runtime packet templates
belong to the package that owns the runtime, not this knowledge layer.

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
`methods/knowledge_provenance.md`. Summarize and transform them into locally reviewed
engineering knowledge; do not copy substantial third-party material or erase
its origin.

## Legacy Path Mapping

The following old paths were consolidated during the 2026-07 migration:

| Old path family | Current path |
| --- | --- |
| Root method documents | `methods/` |
| `skill_engineering/` | `methods/skill_engineering/` |
| `case_studies/`, `experiments/`, `reports/` | `evidence/` |
| `plans/`, `external_knowledge/` | `proposals/` |
