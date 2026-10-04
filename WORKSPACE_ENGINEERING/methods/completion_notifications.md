# Completion Notifications

Claude Code `Stop` hooks are per-turn completion hooks, not process-exit hooks.
Use `SessionEnd` for terminal/session teardown and `Stop` for "the main agent
finished responding" workflows such as long-task completion notifications.

The durable pattern for completion notifications is:

1. Record a per-session start timestamp on `UserPromptSubmit`.
2. Preserve an existing active start timestamp for the same session. Long
   background or monitor work can emit task-notification prompts that also fire
   `UserPromptSubmit`; those must not reset the clock just before `Stop`.
3. On `Stop`, read the matching session state, calculate elapsed time, and
   notify only after the agent is actually done.
4. If `background_tasks` are present, keep the state file and skip notification
   so a paused session with pending work is not announced as complete. Log
   `session_crons`, but do not treat their mere presence as pending work.
5. Run the delivery command synchronously enough that Claude Code does not
   discard a fire-and-forget child process during hook shutdown. Give cold MCP
   startup a realistic timeout.
6. Write compact hook diagnostics outside the source tree, such as under
   `%TEMP%\claude-code-notifications`, so delivery failures are distinguishable
   from hooks not firing.
7. Match the actual local bridge framing. The Hermes CLI `mcp serve` endpoint
   currently uses newline-delimited JSON-RPC on stdio; a `Content-Length`
   framed client will hang on `initialize` and may only surface as a timeout.
8. Keep user-level settings installation explicit and reversible; tracked
   workspace source should provide the repair kit, while writes to
   `%USERPROFILE%\.claude` remain user-approved environment changes.

When a notification is not delivered, debug the chain in order instead of
retesting the whole long task:

- Hook installation: `scripts/platform/install_claude_long_task_notifications.ps1`
  should report both scripts and settings current. Hash-only checks can be
  fooled by line endings, so compare normalized text for managed hook scripts.
- Start state: `UserPromptSubmit` can receive stdin JSON that Windows
  PowerShell cannot decode cleanly when long non-ASCII prompts are present.
  Hooks must fall back to ASCII fields such as `session_id` and log parse
  failures without surfacing a non-blocking hook error.
- Elapsed time: monitor/background work can emit internal task-notification
  prompts. If the start hook overwrites the active state, `Stop` will see only
  the final short turn and skip Hermes because the duration appears below the
  threshold.
- Stop gating: a non-empty `session_crons` field is not proof that work is
  still running. Use `background_tasks` for pending-work suppression and log
  cron counts only as context.
- Hermes startup: if `hook-events.log` shows `hermes-finished ... exit=1`,
  inspect `hermes-mcp-client.log` before changing hooks. An `initialize`
  timeout usually means the local bridge framing is wrong, not that QQBot is
  unreachable.
- Target resolution: prefer resolving short names such as `qqbot` through
  `channels_list`; send to the returned full target when there is exactly one
  channel. A self-test should print success visibly while avoiding
  `messages_send`.
- Final delivery: only after `messages_send` returns success and the log says
  `sent target=...` should a missing phone notification be treated as a
  downstream QQBot delivery issue.
