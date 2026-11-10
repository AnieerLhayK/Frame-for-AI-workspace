# Harness Profiles

This library collects reusable, attributed agent-harness references. It is
methodology, not a grant of authority or proof that a runtime loaded a profile.
The current Workspace manifest, agent registry, task records and policies remain
authoritative when a profile or external source differs.

| Profile | Purpose | Local references |
| --- | --- | --- |
| [Codex](codex.md) | Default target for the proposed DeepSeek adaptation. | Root `AGENTS.md`, Workspace task and skill routes, Codex quick start. |
| [Claude Code](claude_code.md) | Additional host conventions and project-boundary reference. | Claude Code quick start and registered Workspace boundary. |
| [DSH private rules](dsh.md) | DSH-specific entrypoint pointing to the Codex methodology and Workspace authority. | Desktop instruction loading remains subject to runtime verification. |

The intended DSH default is the reviewed Codex adaptation, subject to the
separate Desktop runtime and plugin validation. Source updates require a change review
before changing an active adaptation; upstream prose and host-specific defaults
must not silently extend Workspace permissions.

Each profile points to authoritative material instead of copying it. External
sources are references, not locally validated behavior. Runtime instructions
should load only the pointers and branch-specific material relevant to the task.

## Source drift preview

`sources.yaml` lists bounded local and official sources. To compare them with
previously reviewed text snapshots, run:

```powershell
workspace knowledge harness-check --baseline <reviewed-snapshot-directory> --online --format json
```

Each snapshot is a UTF-8 file named `<source-id>.txt`. Changed sources produce a
bounded unified diff. A `review.json` file must contain `status: reviewed` and a
`sources` object mapping each source ID to the SHA-256 of its UTF-8 snapshot.
Missing or mismatched markers and snapshots are `UNREVIEWED`; an offline remote
source with a valid marker is `NOT_CHECKED`. The marker records review state,
but is not independent proof of reviewer identity or authority. The command
never creates or changes a baseline or activates a profile. Network fetches are
restricted to the listed official HTTPS hosts, including redirects.

On the owner-local DSH Desktop profile, `workspace-kit` starts a read-only
online check at startup and every 24 hours while the host remains running. The
`workspace_harness_status` tool shows its most recent result and bounded diffs;
an explicit refresh runs it again. The first snapshots are a pending-review
candidate in DSH-private state, so their status stays `UNREVIEWED`, even when
the source matches. They may still show diffs. No automatic check edits a
baseline, installs an update, or changes a profile. Actual authenticated
Desktop loading must still be verified; a mocked-host integration check passed.
