# Skill Design Patterns

Skills should have narrow contracts. The more a skill mutates state, the more it needs protocol references, validation, and handoff discipline.

## Generator Skill

- Good for: creating initial structured outputs, scaffolds, templates, and starter packs.
- Not good for: long-term per-instance evolution or one-off runtime fixes.
- Collaborates with: maintainer skills through generalization backlog and accepted lessons.

## Maintainer Skill

- Good for: narrow patches, consistency repair, evolution decisions, and validation notes.
- Not good for: broad template redesign without explicit scope.
- Collaborates with: diagnosis skills through handoff packets and with generators through generalization notes.

## Diagnosis Skill

- Good for: classifying drift, gathering evidence, naming failed layers, and recommending patch scope.
- Not good for: applying patches directly.
- Collaborates with: maintainers by producing diagnosis and handoff packets.

## Runtime Character Skill

- Good for: user-facing voice, style, and task performance.
- Not good for: owning its own long-term maintenance protocol.
- Collaborates with: style-doctor for drift diagnosis and maintainer for evolution.

## Governance Skill

- Good for: checking boundaries, maintaining protocol consistency, and preserving workspace hygiene.
- Not good for: changing domain behavior without domain ownership.
- Collaborates with: validators, reports, and project context.

## Validator Skill Or Script

- Good for: checking file existence, references, required contracts, and obvious drift.
- Not good for: understanding all semantic intent.
- Collaborates with: humans and maintainers by producing clear errors, warnings, and snapshot reports.

## Collaboration Rule Of Thumb

Keep responsibility handoffs explicit:

```text
diagnose -> decide -> patch -> validate -> generalize only if justified
```

When a skill seems to need all roles at once, split the workflow before the behavior becomes impossible to audit.

---

## Patterns From Experience

### 4D Contract Decomposition

The workspace evolved from a flat skill descriptor to four independent dimensions:

```yaml
role:              # what the skill does in the ecosystem
authority:         # what durable effects it may produce
execution_modes:   # task-level activation of text/record/source behavior
exposures:         # which platform projections can discover it
```

Each dimension is independently decoupled. A skill can be exposed on Codex, OpenCode, and Claude without gaining any new authority. It can have `text_only` execution mode while retaining a `generator_write` authority (authority is the ceiling, execution mode is the active grant).

### Exposures Are Not Authority

- A skill exposed on multiple platforms does not gain write access on any of them.
- A skill may be invisible on all platforms (no exposures) and still process handoff packets.
- Exposure is a routing concern, not a security or ownership boundary.

### Authority Levels In Practice

| Authority | Meaning | Example |
| --------- | ------- | ------- |
| `runtime_output_only` | Text output only; no filesystem writes | ZYC runtime character |
| `diagnosis_record_write` | May write diagnosis packet files | Style doctor |
| `source_patch` | May edit existing source files | Character maintainer |
| `generator_write` | May create new generated skills | Character generator |

The execution_mode (`text_only` / `record_write` / `source_patch`) must be within the skill's authority. A `runtime_output_only` authority cannot activate `source_patch` mode.

