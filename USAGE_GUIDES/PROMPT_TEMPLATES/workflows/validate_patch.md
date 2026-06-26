# Workflow Prompt: Validate Patch

Use after a maintainer patch on any compatible platform.

```text
Validate the recent character-maintainer patch.

Target character:
<absolute path>

Linked patch note:
<path or id>

Test prompt:
<prompt>

Before behavior:
<summary or excerpt>

Expected after behavior:
<criteria>

Please:
1. Re-read changed files and adjacent files.
2. Check for contradictions with voice, style, anti-patterns, rubric, and prompts.
3. Run any available lightweight checks.
4. Write a validation note or validation summary.
5. State pass_or_fail.

Do not add new patch changes unless validation reveals a small obvious fix and I approve.
```
