# Workflow Prompt: Diagnose Runtime Drift

Use on a platform where `style-doctor` is exposed. Its authority remains diagnosis-only.

```text
Use style-doctor.

Runtime failure:
<describe what happened>

Character:
<character id>

Task type:
<task type>

Failed output excerpt:
<excerpt>

Expected direction:
<expected style or behavior>

Please:
1. Classify drift types.
2. Identify the failed layer.
3. Cite evidence.
4. Assign severity.
5. Recommend patch scope.
6. Produce a diagnosis packet.
7. Produce a handoff packet if maintainer work is needed.

Do not patch files.
Do not create patch notes, validation notes, generalization notes, or patch ledger entries.
Do not mark accepted/rejected/deferred; leave maintainer decisions to character-maintainer.
Use workspace-relative source paths in handoff recommendations.
```
