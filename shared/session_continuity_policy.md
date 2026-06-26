# Session Continuity Policy

Source directory moves must not make Claude Code or OpenCode conversations
unrecoverable.

## Storage Boundary

Conversation stores are external runtime data. Their current machine locations
belong in `workspace_manifest.yaml -> session_stores`; transcripts and databases
must not be copied into the Git source tree.

## Migration Rule

Before moving a directory that may have been used as an agent working directory:

1. Inventory sessions that reference the old path.
2. Create a consistent external backup without overwriting the live store.
3. Export tool-supported portable session files when available.
4. Record old-to-new path mappings in
   `PROJECT_CONTEXT/session_migrations.json`.
5. Move source and rebuild platform projections.
6. Run `python scripts/workspace_cli.py sessions audit`.

Do not rewrite vendor databases or transcript files merely to replace an old
path. Historical working-directory fields may remain old when the tool still
associates the session with the same repository or project identity.

## Tool-Specific Recovery

### Claude Code

Claude Code commonly groups conversations by project root. If a move stays
inside the same project root, preserve the existing project bucket and verify
that its JSONL transcripts remain readable. Resume a known conversation by
session ID when directory-based continuation does not surface it.

### OpenCode

OpenCode sessions belong to a project and also retain the directory from which
the session started. A moved subdirectory may therefore remain as historical
metadata. Preserve the database, export affected sessions with `opencode
export`, and resume by session ID when needed.

## Destructive Boundaries

- Never delete a live session store as part of a source migration.
- Never replace the live database with a backup during routine validation.
- Never import exports over existing sessions without a separate recovery task.
- Keep migration backups until the new layout has been used successfully and
  the user explicitly approves retention cleanup.
