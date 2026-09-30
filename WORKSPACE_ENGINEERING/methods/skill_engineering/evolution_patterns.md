# Evolution Patterns

Skill evolution works best when it is incremental, recorded, and separated from generation.

## Runtime Drift Repair

Treat drift as evidence first, not as permission for broad rewrite. Capture failed output, expected direction, failed layer, and severity.

## Gradual Refinement

Skills often improve through small changes to prompts, references, checklists, or policies. Each change should preserve existing useful behavior unless the user asks for redesign.

## Small Patch Strategy

Prefer local patches that target the observed failure. Record why the patch is narrow and how to roll it back.

## ZYC Evolution

ZYC is a runtime character skill with specific style material. Its evolution can teach useful lessons, but those lessons should not automatically change generator templates.

## Generator Generalization

Only generalize a maintainer patch when the lesson is truly reusable across future generated skills. Use a generalization note and backlog before generator changes.

## Not Every Lesson Becomes Logic

Some lessons belong in docs, rubrics, examples, or future maintainer judgment. Turning every lesson into generator logic can make the generator rigid and overfit.

---

## Patterns From Experience

### Evidence-Aware Interaction Scaffold (GEN-20260613-001)

The first completed ZYC generalization added interaction scaffolding to the character generator:

**What was generalized:**

- Provisional interaction posture and inference discipline to generated voice cards.
- Candidate-domain and task-intensity guidance to generated style profiles.
- Context-sufficiency checks in generated discussion prompts and SKILL checks.
- Premature inference and false-domain-certainty anti-patterns.

**What was NOT generalized (local boundary):**

- ZYC's relationship posture, social values, preferred imagery, and emotional asymmetry.
- ZYC-specific patriotic or stylistic traits.
- Topic-frequency-based worldview or competence claims.

**Implementation pattern:** Reuse existing generated files and templates. Do not add required config fields, change output directory structure, or require user review beyond subjective character fit. Keep independent agent checks for facts, privacy, safety, and maintainability.

Validated with 10 tests passing, protocol validator at 0 errors, and `git diff --check` clean.

### Generalization Note Handles Both States

The GEN-20260613-001 record was completed (backlog=false, accepted=true) — meaning the generalization was already implemented and validated. This is a valid state. The generalization backlog directory contains:

- **Proposed generalizations** (backlog=true): lessons identified but not yet implemented.
- **Completed generalizations** (backlog=false, accepted=true): lessons that were implemented and validated as generator changes.

Both states use the same note format. Consumers should check `decision.accepted` (was the lesson accepted by the maintainer?) and `decision.backlog` (is implementation pending?) to understand the current state.

### Evolution Precedence Pattern

The evolution flow demonstrated by ZYC cases 004, 006, 007, 009 shows a pattern for character evolution:

```text
1. Runtime failure in specific case
2. Style-doctor diagnosis (focused on the interaction layer)
3. Handoff to character-maintainer
4. Maintainer decides: character-local fix or broader generalization?
5. If local: narrow patch + validation
6. If generalizable: generalization note → generator changes → revalidation
```

The key decision point is step 4: not every character fix should touch the generator. The generalization note formalizes this gate.

