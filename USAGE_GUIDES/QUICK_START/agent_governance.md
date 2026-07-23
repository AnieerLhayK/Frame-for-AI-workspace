# Agent Governance

Use this interface when an agent wants to write to the workspace and you are
unsure whether the target is a record, skill source, or structural file.

## View The Matrix

```powershell
workspace agent status
```

## Inspect Registrations

```powershell
workspace agent list
workspace agent show codex
workspace agent validate codex
workspace agent doctor cursor
```

- `list` gives status, identity type, effective Role, owner, and expiry.
- `show` displays the complete contract plus its effective downgraded view.
- `validate` checks identity, alias, lifecycle, capability, scope, platform,
  storage, and Session declarations.
- `doctor` also checks current Manifest/platform consistency and materialized
  local boundaries.

`WARNING` means low-permission use may continue. `ERROR` blocks declared
registration authority. Unknown, proposed, invalid, suspended, and retired
agents are treated as Consumer.

## Check A Write

```powershell
workspace agent check --agent hermes --path workspace_manifest.yaml
workspace agent check --agent hermes `
  --path packages/character-system/reports/runtime-loop/diagnoses/DIAG-demo.md
```

The first check is denied because the manifest is structural. The second is
allowed because Hermes is a bounded record producer.

When a Skill is actively driving the operation, include it in the decision:

```powershell
workspace agent check --agent hermes --skill zyc `
  --path packages/character-system/runtime/characters/zyc/references/voice_card.md

workspace agent check --agent hermes --skill style-doctor `
  --path packages/character-system/reports/runtime-loop/diagnoses/DIAG-demo.md
```

The first command must DENY: Hermes lacks `source_write`, and ZYC permits only
`text_only`. The second may ALLOW because both Hermes and style-doctor permit a
scoped diagnosis record.

Hermes also has a runtime guard connected to `pre_tool_call`. It blocks native
file writes, every non-allowlisted terminal command, Skill management, code
execution, and mutating MCP actions before they touch workspace source.
Action-based MCP tools must expose a resolvable external output path or fail
closed. A short `pre_llm_call` context explains the correct route, but the hook
is the actual boundary.

## Reapprove A Changed Hermes Guard

Changing the tracked guard script intentionally invalidates its Hermes
allowlist approval. Inspect the exact three configured hooks first; this is a
dry run and writes nothing:

```powershell
workspace agent approve-hermes-guard
```

After a reviewed script change, use an active task record that includes
`external_write` and make the external write explicit:

```powershell
workspace agent approve-hermes-guard --approve --record-id <TASK-ID>
```

The command accepts only the configured `pre_tool_call`, `post_tool_call`, and
`pre_llm_call` workspace guards. It refuses missing or ambiguous hooks and
preserves unrelated Hermes allowlist entries. It never changes the hook
commands, MCP permissions, or guard policy.

OpenCode and Reasonix use the same record-producer authority:

```powershell
workspace agent check --agent opencode --skill zyc `
  --path packages/character-system/runtime/characters/zyc/SKILL.md
workspace agent check --agent reasonix --skill style-doctor `
  --path packages/character-system/reports/runtime-loop/diagnoses/DIAG-demo.md
```

The first command must DENY and the second may ALLOW. OpenCode enforces this
through `opencode.json` plus its project plugin; Reasonix uses `reasonix.toml`
permissions and bounded filesystem roots. These are repository-local adapters,
so using either executable from another project does not automatically apply
this workspace's authority contract.

## Submit A Request

```powershell
workspace agent request --agent hermes --mode review_only `
  --summary "Register a missing skill exposure" `
  --path workspace_manifest.yaml
```

The request is written under `reports/agent-requests/`. It records intent but
does not authorize the change.

Use `--mode worktree` when the agent should implement a reviewed change in an
isolated Git worktree. Use `--mode temporary_lease` when a short-lived external
capability lease is more appropriate.

## Validate A Lease

```powershell
workspace agent lease validate ${DATA_ROOT}/workspace-governance\leases\LEASE-....yaml
```

Structural leases require a worktree, exact path scopes, a trusted issuer, and
an expiry no more than 24 hours after activation. The workspace does not
automatically issue or merge leases.

The interface also does not activate, suspend, retire, install, expose, or
delete agents. Those remain reviewed governance changes.

## Testing A Candidate

A testing registration must use an exact, expiring scope such as:

```text
reports/agent-experiments/<agent-id>/**
```

It may not inherit a full role or receive `structural_write` or
`platform_write`. Registration never creates external cache or Session data.
