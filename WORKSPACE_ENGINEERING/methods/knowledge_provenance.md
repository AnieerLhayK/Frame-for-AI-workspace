# Knowledge Provenance

Reusable engineering knowledge may come from local work, public documentation,
research papers, open-source repositories, issue discussions, or other
practitioners. Origin and confidence must remain visible.

## Required Intake Record

When an external source materially influences a lesson, record:

```yaml
origin_type: official_docs | research | open_source | article | discussion | local_experience
source_title:
source_url:
author_or_project:
license_or_usage_note:
accessed_at:
adaptation:
local_validation: untested | partial | validated | repeated
applicability:
known_limits:
```

The record may appear in a case study, experiment, or a short provenance
section inside the relevant pattern file.

## Transformation Rules

1. Prefer primary sources for technical claims.
2. Attribute the source and link to it when redistribution is permitted.
3. Summarize concepts in original language instead of copying substantial text.
4. Separate what the source claims from what was observed locally.
5. Test compatibility with the current workspace before calling a pattern
   validated.
6. Preserve license notices when code, templates, or structured material are
   adapted.
7. Never import secrets, private conversations, proprietary corpora, personal
   identifiers, or unreviewed generated claims.

## Promotion Path

```text
external reference
-> bounded note or experiment
-> local validation
-> reusable pattern or case study
-> repeated evidence
-> optional public teaching material
```

An interesting GitHub repository is not automatically a local best practice.
External material remains `External reference` until evidence promotes it.

## Public Sharing Check

Before publishing:

- remove machine-local paths or replace them with placeholders;
- remove credentials, Session data, private corpora, and personal metadata;
- verify links, licenses, and attribution;
- state the tested environment and date;
- distinguish policy from advice and fact from inference;
- include failure modes and rollback guidance where relevant.
