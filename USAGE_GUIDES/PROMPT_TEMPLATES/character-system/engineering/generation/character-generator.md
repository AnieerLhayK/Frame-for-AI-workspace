# character-generator Prompt Templates

Current default exposure: Codex. The generator role and authority are platform-independent.

## Generate A New Character

```text
Use character-generator.

Workspace source root:
<workspace-root>

Generator root:
<workspace-root>\packages\character-system\engineering\generation\character-generator

Character id:
<character_id>

Display name:
<display_name>

Corpus folder:
<workspace-root>\packages\character-system\engineering\generation\character-generator\corpus\<character_id>

Config file:
<workspace-root>\packages\character-system\engineering\generation\character-generator\configs\<character_id>.json

Task:
Create or verify the config, ingest the authorized corpus, and build the character skill.

Run:
python scripts\build_character.py --config configs\<character_id>.json

Expected output:
<workspace-root>\packages\character-system\engineering\generation\character-generator\characters\<character_id>

Guardrails:
- Use only authorized corpus material.
- Do not place private corpus material in Git.
- Keep generated output style-inspired, not identity impersonation.
- Include bounded chat/discussion support when the character is meant to respond to user thoughts, not only transform text.
- Do not modify existing mature characters such as zyc.
- Do not edit character-maintainer or style-doctor.

Before finishing:
- Summarize generated files.
- Report validation result.
- Tell me whether the output is ready to expose to OpenCode.
- Do not commit unless I explicitly ask.
```

## Update A Generated Character From Corpus

```text
Use character-generator.

Target config:
<workspace-root>\packages\character-system\engineering\generation\character-generator\configs\<character_id>.json

Updated corpus:
<workspace-root>\packages\character-system\engineering\generation\character-generator\corpus\<character_id>

Task:
Rebuild this generated character from config and corpus.

Run:
python scripts\build_character.py --config configs\<character_id>.json

Guardrails:
- This rebuild may overwrite generated output under characters\<character_id>.
- Do not apply this to manually evolved characters unless I explicitly approve.
- Do not infer private facts from the corpus.
- Do not commit corpus files.

Output:
- Build result.
- Validation result.
- Files changed summary.
- Any privacy or generation warnings.
```

Resolve `<workspace-root>` from `workspace_manifest.yaml -> workspace.source_of_truth`.
