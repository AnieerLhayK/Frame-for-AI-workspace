# Workflow Prompt: Patch Existing Character

Use on a platform where `character-maintainer` is exposed, with `source_patch` mode explicitly justified.

```text
Use character-maintainer.

Target character folder:
<absolute path>

Diagnosis or handoff:
<path or pasted packet>

Patch intent:
<what should improve>

Allowed files:
<list>

Do not touch:
<list>

Please:
1. Verify the diagnosis.
2. Record accepted/rejected/deferred.
3. If accepted, patch the smallest responsible surface.
4. Write a patch note.
5. Validate the changed behavior.
6. Write a validation note.
7. Recommend whether a generalization note is needed.

Do not:
- Rewrite the whole character.
- Edit character-generator.
- Edit unrelated shared protocols.
- Commit without approval.
```
