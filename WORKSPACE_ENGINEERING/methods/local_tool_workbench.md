# Local Tool Workbench Patterns

These patterns describe turning personal AI-tool commands into a maintained
desktop workbench. They come from the Commander → muti-ai case and subsequent
tool-update work. They are guidance, not additional workspace policy.

- Evidence level: Validated locally for the delivered workbench; Observed for
  unresolved update findings.
- Applicability: a small Windows GUI coordinating existing CLIs and services.
- Case and verification limits: `WORKSPACE_ENGINEERING/evidence/commander_to_muti_ai.md`
  in the authoritative workspace. Public architecture projections omit local
  evidence; the verification limits are also stated below.

## Deliver A Vertical Slice Before Broadening The Product

- What: progress from an explicit command, to a simulated interaction, to one
  real service, then a usable local entry and an independent export.
- Why: each slice answers a different question: can the interaction work, can
  the process be controlled, can the owner use it, and can a clone reproduce it?
- When useful: a personal script starts accumulating controls and maintenance.
- Risks: a polished mockup can be mistaken for a connected product.
- Common mistakes: adding categories, installers or a plugin framework before
  proving the first real launch and stop.

State acceptance in observable terms. “A single desktop entry opens a window
with independent controls” is more useful than “improve the launcher.” Name the
entry, define open/close behavior, and distinguish simulation from real mode.
Reserve new integrations for later slices rather than creating inactive switches.

## Separate Window, Operation And Service Lifetimes

- What: the window renders state; a Controller owns each tool's operations;
  an Adapter hides runtime details; a detached worker continues service work.
- Why: closing the GUI should not silently stop a service or abandon a start.
- When useful: launchers manage long-running processes with delayed readiness.
- Risks: detached workers add locking, state recovery and deployment complexity.
- Common mistakes: using a GUI boolean as runtime truth or killing every process
  named Node or Python during stop.

Keep the control Interface small: start, stop and state observation. Use a
controlled test Adapter and a demo Adapter at the same boundary as real runtime
access. Do not introduce a general plugin system for two integrations.

Maintain one owner per tool, reject repeated in-flight requests, and recheck
process identity before termination. PID alone is insufficient; command,
executable, creation time and profile can distinguish an unrelated or reused PID.
Opening, folding and recoloring the window must not submit service operations.

## Model Process State And Connection Evidence Separately

| Evidence | What the UI may claim | What still needs checking |
| --- | --- | --- |
| Installer or launcher process exists | Starting | Service process and readiness |
| Identified service process exists | Running; connection unconfirmed | Provider readiness or client connection |
| Authorization is requested | Waiting for authorization | Human verification and successful connection |
| Connection is lost but process lives | Running with connection warning | Recovery or an explicit stop |
| A client completes a bounded operation | That operation succeeded | Broader capabilities and future reliability |

A failed stop retains the confirmed running state and offers retry. A timeout
requires another observation; it does not justify a second launch. Unknown or
ambiguous state should disable the affected control and explain the uncertainty.

Terminal launchers use a different contract: “terminal opened” confirms dispatch,
not model readiness. Capture the selected project directory when submitting the
request. New/resume actions should retain the CLI's account, permissions and
history semantics rather than becoming service toggles.

## Preserve Diagnostic Meaning Without Persisting Secrets

Normalize known failures into bounded categories and an exit code. Keep raw
authorization output, device codes, tokens and account identifiers out of durable
logs. Unknown output remains unknown rather than becoming a guessed explanation.

Read the last output before finalizing a failed start. Process exit can precede
reader completion; use asynchronous completion, a bounded drain deadline and
reader generations so a previous attempt cannot contaminate a retry. Exercise
these orderings with controlled delays.

For network failures, check each dependency using the actual child runtime.
Reaching a public landing endpoint does not prove a session backend is reachable.
Test existing proxy inheritance at the launch boundary; preserve explicit
overrides and keep a justified correction local to that child environment.

## Let Catalog And Preferences Organize Existing Controls

Register stable category IDs, names and launcher membership in a small Catalog.
Rendering can then move from two rows to collapsible groups without changing
service control. An empty category should say it has no launcher.

Merge preferences rather than replacing the entire file. Distinguish missing
expansion preferences from an explicit empty list, ignore unknown IDs, and keep
theme changes independent of project history. Test hidden controls: folding a
category must preserve pending operations, errors and observation updates.

Qt offscreen tests establish interaction and state behavior. Native window
inspection establishes layout, focus and scaling behavior. Real process checks
establish lifecycle behavior. Report these separately; none substitutes for the
others or for a provider-client check.

## Make Local Usability And Public Reproduction Separate Deliverables

Keep source, tests, resources and portable maintenance instructions in the
package. Keep machine configuration, credentials, state, logs and rollback
archives in an external data root. Reuse a verified runtime when suitable;
installation is a separate change with its own evidence and authority.

Before publishing, export a complete allowlisted file set into staging, validate
references and forbidden content, then run simulation from that export. A clean
clone should not need private workspace governance files. Preserve workspace
source authority through a registered publisher and independent projection
history; record source revision without private remotes or machine paths.

Public CI should validate portable boundaries and simulation without credentials
or real service starts. Native deployment and account authorization remain local
acceptance. A personal helper README should state its tested scope and limits.

## Update Tools Against Behavior, Not A Version String

1. Pin the intended official release and resolve conflicting version channels.
2. Inspect existing runtime, storage links, active consumers and rollback needs.
3. Reproduce migrations with synthetic configuration and credentials, including
   ordinary and linked paths where those are real deployment conditions.
4. Verify effective permissions using actual refusal results. A valid config
   file or successful diagnostic command does not prove runtime enforcement.
5. Prepare dependencies before downtime. Rebuild a virtual environment at its
   final path when launchers encode absolute interpreter paths.
6. Stop only freshly identified consumers, preserve installation and coherent
   data snapshots, then verify the final entry and restore prior services.
7. Report updated, repaired, rolled back and deferred outcomes separately.

Do not convert a failed update into a successful delivery merely because the
package installed. CI also exercises deployment assumptions: test the oldest
supported Python, explicit branch conditions and missing optional dependencies.
Link checks must remain conservative when an API is unavailable; help commands
should not need unrelated conversion dependencies.

## Provenance And Limits

Origin: local implementation, diagnosis, review and acceptance records summarized
in the linked case. No third-party code or documentation is reproduced here.
The workbench architecture was validated locally; unresolved update experiments
support the verification method, not a claim that those tools are repaired.
These patterns do not establish a security sandbox or universal Windows support.
