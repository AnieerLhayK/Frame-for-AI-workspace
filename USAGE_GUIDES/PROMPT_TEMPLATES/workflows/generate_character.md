# Workflow Prompt: Generate Character

Use on a platform where `character-generator` is exposed.

```text
Use character-generator.

Goal:
Generate a new platform-neutral character skill package.

Character id:
<character_id>

Display name:
<display_name>

Authorized corpus location:
<workspace-root>\packages\character-system\engineering\generation\character-generator\corpus\<character_id>

Config location:
<workspace-root>\packages\character-system\engineering\generation\character-generator\configs\<character_id>.json

Output location:
<workspace-root>\packages\character-system\engineering\generation\character-generator\characters\<character_id>

Please:
1. Inspect whether the corpus folder and config exist.
2. If the config is missing, create it from the example schema with conservative defaults.
3. Run the build command.
4. Report validation, privacy, and output status.

Do not:
- Commit corpus files.
- Use unauthorized source text.
- Generate an impersonation skill.
- Modify maintainer or runtime character skills.
```

Resolve `<workspace-root>` from `workspace_manifest.yaml -> workspace.source_of_truth`.
