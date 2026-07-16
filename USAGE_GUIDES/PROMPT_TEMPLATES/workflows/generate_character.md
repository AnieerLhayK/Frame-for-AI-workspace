# Workflow Prompt: Generate Character

Use on a platform where `character-generator` is exposed.

```text
Use character-generator.

Goal:
Generate a new platform-neutral character skill package from conversational
intake. Do not require me to hand-write JSON.

Required information I can provide:
- Character id, if already decided:
- Display name:
- Authorized corpus source paths:
- Source roles and types:
- Authorization confirmation:
- Privacy boundary acceptance:
- Target tasks or interaction type:

Optional information I can provide:
- Output folder:
- Language:
- Privacy level:
- Style strength:
- Quote policy:
- Personal profile / background orientation:
- Desired relationship posture:
- Source normalization preferences:
- README generation preference per source:
- Speaker/context-note rules:
- Extra forbidden tasks or postures:

Additional requirements:
- Strengths I want the character to have:
- Things it should avoid:
- Successful-output examples:
- Sensitive topics or boundaries:
- Other constraints:

Please:
1. Check required information first.
2. Stop with a missing-info report if required information is incomplete.
3. Use safe defaults for missing optional information.
4. Run the conversational intake build path.
5. Report validation, privacy, output status, and maintainer follow-up needs.

Do not:
- Commit corpus files.
- Use unauthorized source text.
- Generate an impersonation skill.
- Modify maintainer or runtime character skills.
- Create source README files unless requested.
```

Resolve `<workspace-root>` from `workspace_manifest.yaml -> workspace.source_of_truth`.
