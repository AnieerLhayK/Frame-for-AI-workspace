# Agent Governance Policy

This policy separates access to skills from authority over the workspace.
Discovering or invoking a skill never grants permission to register that skill,
edit workspace structure, or change a platform projection.

## Surface Classification

| Surface | Examples | Required capability |
| --- | --- | --- |
| Platform projection | `.claude/skills/`, manifest platform roots, registered public projections | `platform_write` |
| Proposal record | `reports/agent-requests/` | `proposal_write` |
| Runtime record | diagnosis, handoff, approved runtime-loop records | `record_write` |
| Generated snapshot | current reports under root `reports/` | `report_write` |
| Skill source | `skills/`, package runtime and engineering source | `source_write` |
| Governance structure | manifest, `shared/`, `scripts/`, `PROJECT_CONTEXT/`, root governance files | `structural_write` |

The ordered machine-readable form is `shared/agent_governance.yaml`.

`reports/agent-requests/` is a durable proposal surface and may be empty when
there are no pending requests. `reports/agent-experiments/` is an opt-in,
bounded testing surface and is also allowed to remain empty. Neither directory
is a current snapshot collection. Historical Hermes diagnostics belong under
`PROJECT_CONTEXT/reports/history/hermes/`; `reports/hermes/` is retired and is
not an Agent write target.

### Managed Public Publishers

The public projections for Frame for AI Workspace, Chatty Ch System, and
qq-chat-raw-filter are not generic external-environment writes. Each is a
registered platform projection with exactly one publisher script, disposable
staging path, and approved Git remote URL. Every publisher invocation must satisfy
all of the following before it creates a checkout, commits, or sends data:

1. the staging path and remote URL exactly match its declared publisher;
2. the invoking agent has `platform_write` and the path is inside its scope;
3. an active task record declares `external_write` for the external release;
4. the publisher's normal projection checks pass.

Custom staging paths or remote URLs are rejected by the managed publishers;
use a separate inspection workflow when a temporary local copy is needed. They
cannot be used to bypass the registered publication target.

After an applicable workspace source change is fast-forwarded to `main`, the
maintainer must invoke `scripts/sync_public_projections.py --push` with an
active `external_write` record. That orchestrator discovers every registered
publisher from `managed_platform_publishers`, so adding a future projection to
the registry automatically adds it to the required synchronization step. It
always regenerates and verifies each selected projection; a clean projection
simply produces no remote commit. Direct edits to public checkouts remain
forbidden.

Concrete identities do not live in that policy. They live in
`shared/agent_registry.yaml`, which records status, registration type, aliases,
host classification, exact scopes, platform references, storage boundaries,
and lifecycle review data.

```text
Agent Registration Contract
-> capability and surface policy
-> manifest-backed platform verification
-> runtime access check
```

## Default Agent Classes

| Agent class | Default agents | Allowed durable effects |
| --- | --- | --- |
| Structural maintainer | Codex, Claude Code | Records, skill source, workspace structure, reviewed platform deployment |
| Record producer | Hermes, OpenCode | Scoped diagnosis, handoff, agent report, and change request records |
| Consumer | Unregistered agents | Read, temporary invocation, and change requests only |

Agent identity does not replace a skill's own role and authority. For example,
Hermes may invoke `style-doctor` and write a diagnosis in the declared runtime
record scope, but it may not edit the doctor source or register a missing
projection.

## Registration Lifecycle

Supported states are:

```text
proposed -> testing -> active -> suspended | retired
```

- `proposed` is always effective Consumer access.
- `testing` requires explicit capabilities, exact paths, and an expiry. It
  cannot inherit a whole role or obtain structural/platform write authority.
- `active` requires a valid identity contract, owner, review timestamp, policy
  role, platform references, and clean validation.
- `suspended` and `retired` are effective Consumer access and may not retain
  active lease references.
- Invalid or incomplete registrations degrade to Consumer. Missing values never
  expand authority.

Registration status is not identity proof. The registry is a reviewed local
contract; the current CLI cannot cryptographically prove which model or process
is invoking it.

## Platform Adapters And Candidates

Hermes, OpenCode, and Reasonix are active `record_producer` agents. They share
the same workspace authority but enforce it through platform-specific project
adapters: Hermes hooks, an OpenCode plugin plus project permissions, and
Reasonix project permissions plus a bounded sandbox and filesystem MCP.

Cursor remains a proposed `agent_host`. Until a tested workspace adapter can
bind its tool calls to this policy, it resolves to Consumer and must not receive
workspace write capabilities. Candidate testing output belongs only under an
exact `reports/agent-experiments/<agent-id>/` scope.

## Missing Registration

When an agent cannot discover a needed skill:

1. It may temporarily read or invoke an explicitly supplied skill when the
   invoking platform supports that operation.
2. It must not edit `workspace_manifest.yaml`, platform roots, junctions, or
   workspace policies to make the registration permanent.
3. It should create a change request with:

   ```powershell
   workspace agent request --agent <agent> --mode review_only `
     --summary "<why registration is needed>" `
     --path workspace_manifest.yaml
   ```

4. Codex, Claude Code, or the user reviews and performs the structural change.

## Temporary Leases

Temporary authority is represented by an external lease file, not a tracked
workspace registration. Lease files belong under the configured external lease
store and must include:

- agent identity;
- issuer and approval;
- exact capabilities and path scopes;
- start and expiry timestamps;
- isolation mode;
- status.

`structural_write` leases require an isolated worktree. A branch name alone is
not isolation because it still changes the current working tree.

Validate a proposed lease before use:

```powershell
workspace agent lease validate <lease-file>
```

The MVP validates leases but does not issue, activate, merge, or delete them
automatically.

## Change Risk And Worktree Guidance

Change risk is derived from the machine-readable `change_risk_policy` and
existing `surface_classes` in `shared/agent_governance.yaml`. Do not maintain a
second path list in this document.

A high-risk path remains editable by Codex or Claude Code when the resolved
task declares it and routed validation passes. Explicit user confirmation is
still required for destructive or externally visible operations such as Skill
deletion or movement, platform projection changes, large moves, external data
migration, bulk cleanup, or Git history rewriting.

`worktree_recommended` is advisory for ordinary maintainers. Use it for
projection changes, Skill moves/deletes, large migrations, concurrent work, or
experiments that could pollute the current tree. A temporary
`structural_write` lease remains the one case where isolation is mandatory.

## Runtime Enforcement

Registration and Skill prose are policy inputs, not enforcement by themselves.
A platform that can mutate files must connect its tool dispatcher to
`workspace agent check` or an equivalent in-process authorization call before
the write occurs.

Native project permissions and MCP root restrictions should narrow the surface
before the shared authorization check. They are defense in depth, not a
replacement for Agent and acting-Skill authority.

Effective write authority is the intersection of:

1. an active task outcome record whose declared operation matches the target
   (`workspace_write` or `external_write`; managed external publishers retain
   `external_write` for release audit);
2. the resolved task write scope;
3. the Agent capability and path scope;
4. the acting Skill execution mode, when a Skill is active;
5. an optional valid lease;
6. the platform tool boundary.

Any DENY blocks the tool before mutation. `workspace agent check` requires
`--record-id` for writes and chooses the matching registration operation from
the target path. Post-change verification accepts `--agent` and `--skill` so
Git evidence can be checked against the same identity and Skill contracts.
Prompt or memory guidance may explain the route, but it must never be the only
boundary.

## Lifecycle

1. **Request**: the agent writes only a proposal record.
2. **Review**: Codex, Claude Code, or the user selects review-only, temporary
   lease, or isolated worktree execution.
3. **Execute**: the agent stays inside the approved capabilities and paths.
4. **Validate**: normal task, test, and Git validation still applies.
5. **Close**: merge or reject the branch; expire and remove the external lease;
   retain only the accepted workspace records and Git history.

Inspect registrations with:

```powershell
workspace agent list
workspace agent show <agent-id>
workspace agent validate <agent-id>
workspace agent doctor <agent-id>
```

These commands inspect and diagnose. They do not activate, suspend, retire,
install, expose, or delete an agent.

## Non-Goals

- This policy does not treat model confidence as authorization.
- It does not make every agent a structural maintainer.
- It does not permit shell or filesystem tools to bypass a denied capability.
- It does not copy skill source into temporary registration directories.
