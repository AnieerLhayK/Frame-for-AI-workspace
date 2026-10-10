# Human-Facing Output Discipline

Choose output guidance according to the reader's task, recurring difficulties,
and existing mechanisms. Each additional instruction should address an observed
gap. This method is optional engineering guidance, not an always-loaded policy.

## Quality Goal

Optimize for relevance, clarity, and usefulness. Length follows the work needed
to explain, decide, diagnose, or act. Preserve necessary derivations,
intermediate explanations, diagnostic distinctions, operational prerequisites,
examples, and material uncertainty.

Remove repeated claims, automatic praise, rhetorical buildup, weak personal
associations, and conclusions that only repeat the answer. Use contrast when
the distinction changes understanding. Use headings, lists, and tables when
they help navigation, comparison, or execution. Editing succeeds when the
reader can still understand the mechanism or perform the operation correctly.

## Responsibilities And Placement

| Mechanism | Responsibility | Reason to add or change it |
| --- | --- | --- |
| ChatGPT Web custom instructions | Default expression across ordinary explanations, learning, analysis, and troubleshooting | Recurring expression problems affect several kinds of conversations |
| Global or project engineering instructions | Authority, validation, delivery completeness, and cleanup of obsolete references after a change | A recurring engineering failure needs an explicit working agreement |
| ADHD output assistance | Reading and execution support, including visible actions, bounded steps, and useful state reminders | The reader benefits from that presentation and explicitly selects it |
| An optional editorial skill | A repeatable review or rewrite of substantial human-facing artifacts | Sustained document-editing demand justifies a distinct workflow |

An ADHD-oriented assistant style can overlap with prose discipline without
covering every long document. Its presentation defaults should follow the
actual task: an explanation still needs its difficult steps, and an evaluation
does not need an invented action checklist.

Keep engineering correctness requirements in their owning rules. When a
mechanism is removed or replaced, updating affected instructions, entry points,
examples, configuration, and dependencies remains part of completing the
change. Pruning prose must preserve those requirements.

For agent-consumed instructions, use the existing
[`writing-for-agents`](../../external-skills/content/writing-for-agents/SKILL.md)
reference for executable steps, authority boundaries, context pointers, and
completion criteria. A future editorial skill would focus on human readability
and explanation quality. Define that distinction before creating it.

## Choose The Smallest Useful Intervention

Start with actual usage. An engineering-focused Codex workflow with existing
delivery rules and reader-oriented output assistance may gain little from
another permanent language contract. Occasional discussion alone does not
justify adding one. A Web workflow used heavily for learning and discussion
may benefit more directly from general expression preferences.

When the same expression problem recurs, retain representative examples and
identify whether its cause is default expression, task instructions, artifact
requirements, or overlapping guidance. Adjust the smallest owning instruction.
Avoid adding a permanent rule for a single awkward sentence.

When substantial document editing becomes recurring work, first compare the
needed workflow with existing capabilities. If a separate skill is warranted,
define its audience, explicit task triggers, preservation requirements, and
completion evidence. Do not make every response trigger an editorial workflow.

Maintain one authoritative location for each requirement. Task prompts should
retain task-specific selection criteria and deliverables rather than copying
general style rules. Cross-platform versions can share intent while keeping
their own applicable behavior; introduce versioned maintenance only when
maintaining several versions becomes a demonstrated need.

## Evaluate When A Problem Triggers Review

Use a small set of real examples representing the affected tasks. Depending on
the problem, include a simple operation, a conceptual explanation or derivation,
troubleshooting, a brief, or an engineering handoff. No periodic test schedule
is required.

1. Identify the repeated problem and the guidance believed to cause or prevent it.
2. Compare representative outputs before and after the smallest proposed change.
3. Check whether repetition, irrelevant framing, and weak associations decreased.
4. Verify that reasoning steps, assumptions, diagnostic branches, prerequisites,
   and limitations needed for understanding or action remain available.
5. Check for regressions such as rigid formatting, abrupt tone, unsupported
   certainty, or skipped steps. Retain the change only when the affected examples
   improve without losing necessary content; otherwise revise or revert it.

A shorter answer is not sufficient acceptance evidence. Record what improved,
what remained necessary, and which tasks were actually checked. Match the
conclusion to that evidence rather than claiming universal effectiveness.

## Provenance And Evidence Limits

- **Origin:** local experience and reviewed instruction-design discussion,
  consolidated on 2026-10-09. The record generalizes the agreed decisions; it
  does not reproduce private conversation text.
- **Observed adoption:** the user reports having enabled Web custom instructions
  covering directness, task adaptation, selective personalization, and removal
  of repetition. Local inspection confirmed existing engineering rules and
  ADHD output-assistance instructions.
- **Validation level:** partial. These observations establish adoption and
  overlapping responsibilities. They do not establish sustained improvement
  in Web responses or automatic loading of assistance in every session.
- **Applicability:** selecting and maintaining human-facing output guidance
  across conversational and engineering tools. Creative writing, casual
  conversation, and explicit style requests may need different pacing and tone.
- **Limits:** the current preference for deferring extra Codex language rules
  follows an engineering-heavy usage pattern. Reassess it when actual usage or
  repeated failures change. This method does not install skills, modify
  platform settings, or turn reader preferences into workspace policy.

External intake record for the reader-assistance concept:

```yaml
origin_type: open_source
source_title: i-have-adhd
source_url: https://github.com/ayghri/i-have-adhd
author_or_project: ayghri/i-have-adhd
license_or_usage_note: MIT; conceptual summary only, no copied rules
accessed_at: 2026-10-09
adaptation: Describe the assistance responsibility and overlap with other output guidance.
local_validation: partial
applicability: Reader-selected assistance in conversational engineering workflows.
known_limits: Instructions inspected; effectiveness across representative tasks remains untested.
```

The reviewed source revision was
`2ed064090711586e0c97a2fbbf15465fe8f1808b`.
