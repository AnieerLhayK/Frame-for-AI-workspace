# Personal Corpus Preparation For Character Skills

Evidence level: Observed local experience.
Origin type: local_experience.

Personal character skills often start from uneven private corpora: formal
writing, chat exports, hand-curated excerpts, personal profiles, and converted
documents. The useful engineering pattern is to treat each source directory as
a small evidence package with its own reading contract before style extraction
starts.

## Directory README As Source Contract

When a corpus directory is hand-curated or structurally uneven, add a local
README near the corpus. The README should explain:

- what the files are and which files are only indexes;
- whether the files are raw, converted, summarized, or manually selected;
- who is speaking in each format;
- which text is author evidence, context evidence, or editor annotation;
- encoding and conversion requirements;
- known spelling, punctuation, paragraphing, or format problems;
- intended role in the generated skill;
- privacy boundaries and forbidden inferences.

This README is not a style profile. It is an ingestion and interpretation
guide. It helps future agents avoid confusing context notes, filenames,
conversion artifacts, and private facts with style evidence.

## Source Role Beats Fixed Weight

Do not assign quality weights only by source type. A chat corpus may be more
important than polished work when the target character is a friend-chat skill.
A formal essay may be more important when the target task is long-form
rewriting or continuation.

Prefer role-based evidence:

- polished works: long-form structure, narrative control, formal argument,
  paragraph movement, scene handling, endings;
- chat records: interaction posture, immediate judgment, oral rhythm,
  emotional pacing, argument under pressure;
- personal profile: stable background and boundaries supplied by the user,
  not inferred from private text;
- annotations: context for interpretation, not primary author voice.

Numeric weights may still be useful for automation, but they should express
task relevance and source role rather than a default hierarchy such as
"formal writing always outranks chat."

## Normalize Without Flattening

Private corpora often contain typos, inconsistent punctuation, incomplete
sentences, and irregular line breaks. Normalization should preserve three
layers:

1. Original text: the reviewed source as supplied.
2. Normalized text: obvious encoding and typo repairs, with speaker/context
   markers made explicit.
3. Analysis notes: why a correction was made and which traits were preserved.

Do not silently polish chat text into formal prose. In chat corpora, short
lines, missing punctuation, repetition, hesitation, and abrupt turns may be
the actual style evidence.

## Personal Profile Belongs Outside Corpus Inference

A personal profile can help a generator avoid over-inference from private
corpus material. Store it separately from source directories, for example:

```text
raw_material/<character-id>/profile.md
raw_material/<character-id>/corpus/work/
raw_material/<character-id>/corpus/chat/
```

Recommended profile fields:

- character build purpose and target relationship, such as friend chat,
  writing assistant, critique partner, or mixed use;
- stable background facts the user explicitly wants available;
- time period or life stage covered by the corpus;
- interests, recurring projects, and writing domains;
- interaction preferences and forbidden postures;
- privacy limits, facts not to infer, and topics that require user context;
- source directories and whether README generation is requested.

The profile should not become an identity simulator prompt. It is a boundary
and orientation file for style-inspired generation.

## Generator Interface Implication

A generator that supports personal corpora should include a corpus-planning
phase before ingestion:

```text
conversational intake
-> required information check
-> optional corpus README generation
-> source profile normalization
-> ingestion and chunking
-> generated skill
-> generated corpus handoff for future maintenance
```

If required information is missing, the generator should stop instead of
guessing. If optional information is missing, it may continue with safe
defaults, then report the missing items and recommend a maintainer follow-up.

## Validation Checklist

- Every source directory has a clear role or an explicit "unreviewed" warning.
- Context notes are not treated as author voice.
- Other speakers are excluded from author style extraction unless the task
  explicitly needs conversation context.
- Absolute local paths stay in ignored local configs, handoffs, or external
  corpus notes, not committed reusable templates.
- Generated skills avoid real-person impersonation and private fact inference.
