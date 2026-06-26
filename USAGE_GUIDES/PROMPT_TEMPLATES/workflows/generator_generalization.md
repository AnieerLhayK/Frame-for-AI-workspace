# Workflow Prompt: Generator Generalization

Use with `character-generator` only after maintainer review and on a declared exposure.

```text
Review this maintainer-approved generalization candidate.

Generalization note:
<path or pasted note>

Linked patch:
<patch id or path>

Source character:
<character id>

Task:
Decide whether this lesson should affect character-generator assets.

Please:
1. Check whether the lesson is truly generalizable.
2. Identify the smallest generator surface if accepted.
3. Reject or defer if it is character-specific or under-evidenced.
4. Do not edit generator files unless I explicitly approve this implementation pass.

Decision options:
- accepted
- rejected
- deferred

Output:
- decision
- reason
- target generator files if accepted
- risk if generalized
- validation plan
```
