# zyc Prompt Templates

Use in Codex or OpenCode after `zyc` is visible in that platform's skill list. The skill remains text-only on both.

## Natural Discussion

Use this first when you want ZYC to respond like a digital-person style voice, not like a writing tool menu.

```text
Use zyc.

Please respond naturally to the following thought.

Do not ask me to choose rewrite / continuation / critique / discussion.
Do not use headings, bullet lists, tables, or scores.
Do not summarize my view back to me in a flattering AI tone.
You may agree, hesitate, question, or disagree where appropriate.
Keep it style-inspired, not identity impersonation.

Input:
<text>
```

## Rewrite In ZYC Style

```text
Use zyc.

Task:
Rewrite the following text while preserving its meaning.

Input:
<text>

Constraints:
- Keep the output style-inspired, not identity impersonation.
- Do not add private facts.
- Do not over-explain the style.
- Preserve the user's requested language and task.

Output format:
Return only the rewritten text unless I ask for notes.
```

## Continue A Fragment

```text
Use zyc.

Task:
Continue this fragment in a compatible voice and rhythm.

Fragment:
<text>

Constraints:
- Continue the emotional and rhythmic direction already present.
- Do not summarize the fragment.
- Do not explain the imitation.
- Do not add private biographical claims.
```

## If Output Feels Wrong

```text
Use style-doctor.

Target skill:
zyc

Observed problem:
<what felt wrong>

Failed output excerpt:
<excerpt>

Expected direction:
<what should have happened>

Task:
Diagnose the drift. Do not patch zyc directly.
```
