# character-generator Prompt Templates

Current default exposure: Codex. The generator role and authority are platform-independent.

## Generate A New Character From Natural-Language Intake

Copy this when you want to create a personal or corpus-based character without
hand-writing JSON. Fill what you know; leave unknown optional fields blank.

```text
Use character-generator.

I want to create a style-inspired character skill from authorized corpus
sources. Please turn the information below into a safe internal intake/build
plan. Do not ask me to hand-write JSON.

Required information:

1. Character identity
- Character id, if I already have one:
- Display name / label I want users to see:

2. Authorized corpus sources
For each source, include as much as possible:
- Path:
- Source type: work / chat / notes / profile / mixed / unknown
- Source role: long-form style, friend-chat core, critique voice, background orientation, etc.
- Include in style extraction: yes / no
- Generate or update a README in this source directory: yes / no
- Speaker rules, if chat-like:
- Context-note rules, if any:
- Other notes:

3. Authorization and privacy
- I confirm I am authorized to use these sources: yes / no
- I accept the boundary that the output is style-inspired only, not identity impersonation: yes / no
- I accept no private fact inference and no verbatim reconstruction: yes / no

4. Target use
- Main target tasks: rewrite / continuation / critique / style transfer / discussion / friend chat / writing collaborator / other
- Typical user situation:
- Desired language:

Optional information:

- Preferred output folder or character id-derived default is fine:
- Privacy level: high / medium / low / use safe default
- Style strength: light / medium / strong / use safe default
- Quote policy or max quote length:
- Personal profile or background orientation supplied by me:
- Desired relationship posture: friend, critic, writing partner, reflective companion, etc.
- Source normalization preferences: preserve typos, clean punctuation, keep chat rhythm, etc.
- Forbidden postures or tasks beyond impersonation/private inference/reconstruction:
- Whether reports should hide external local paths:
- Any source that should be treated as context rather than author voice:

Additional requirements or preferences:

- The generated character should be especially good at:
- It should avoid sounding like:
- Examples of outputs I would consider successful:
- Topics or boundaries that need extra care:
- Anything else I want the build plan to preserve:

Task:
1. Check whether required information is complete.
2. If required information is missing, stop and list exactly what is missing.
3. If only optional information is missing, use safe defaults and report the quality gaps at the end.
4. Build with conversational intake, not manual JSON editing.
5. Produce or update source README files only when I requested them.
6. Generate a corpus reading handoff inside the generated character when source planning is enabled.

Guardrails:
- Use only authorized corpus material.
- Do not place private corpus material in Git.
- Keep generated output style-inspired, not identity impersonation.
- Do not infer private facts from source text.
- Do not quote long private excerpts.
- Do not modify existing mature characters such as zyc.
- Do not edit character-maintainer or style-doctor.

Before finishing:
- Summarize the normalized build plan without exposing private excerpts.
- Summarize generated files.
- Report validation, privacy, and optional-info warnings.
- Tell me whether maintainer follow-up is recommended.
- Do not commit unless I explicitly ask.
```

## Generate A New Character From Config

Use this for repeatable automation when a config already exists.

```text
Use character-generator.

Character id:
<character_id>

Display name:
<display_name>

Corpus folder:
<workspace-root>\packages\character-system\engineering\generation\character-generator\corpus\<character_id>

Config file:
<workspace-root>\packages\character-system\engineering\generation\character-generator\configs\<character_id>.json

Task:
Read the existing config, ingest the authorized corpus, and build the character skill.

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
- If the config is missing, stop and ask whether I want to provide conversational intake or create a config.

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
