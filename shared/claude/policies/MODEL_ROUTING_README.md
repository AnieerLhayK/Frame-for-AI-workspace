# Model Routing Policy Infrastructure

## Overview

This directory provides the shared implementation layer for Claude Code
model-tier recommendations. The complete structure is:

```text
Global Principle
-> Shared Policy
-> Project Override
```

The current shared policy covers model-upgrade decisions for:

- default: `deepseek-v4-flash`
- upgrade: `deepseek-v4-pro`

It provides recommendations only. It does not implement model switching,
observe actual model usage, or modify runtime configuration.

## Why Policy, Not Skill

A Skill is an executable task capability: it teaches an agent how to perform a
kind of work and may include workflows, scripts, references, or tools.

Model routing is a governance decision that applies around task execution. It
answers which model tier appears appropriate. Keeping that decision in a
Policy avoids presenting routing as a user-invoked capability and prevents
model selection from inheriting a Skill's execution authority.

## Three-Layer Responsibility

- Global Rule stores durable principles: prefer an economical default, consider
  a stronger model for materially complex or risky work, never block solely on
  model tier, and never claim an unobservable switch.
- Shared Policy stores the current implementation: model aliases, concrete
  examples, recommendation signals, and message format.
- Project Rule stores local needs: explicit adoption, stricter guidance,
  extensions, or disabling escalation recommendations.

The full Flash/Pro task lists do not belong in the Global Rule because they
change more frequently, consume context in unrelated sessions, and couple all
projects to one provider-specific model pair. Keeping them in the Shared Policy
lets the implementation evolve without rewriting the universal principle.

## Default Behavior and Project Overrides

The user-level principle is on by default, so Claude may consider model tiering
without every project repeating generic guidance. Detailed shared routing is
enabled when a project imports this policy.

Special projects should express their differences in project `CLAUDE.md`. A
project may extend the signals or disable escalation recommendations entirely.
Project-level instructions take precedence for that project.

## Project Integration

1. Decide whether the user-level principle alone is sufficient.
2. To enable concrete Flash/Pro guidance, add an `@path` import to the
   project's `CLAUDE.md`.
3. Keep project-specific overrides beside that import.
4. Start a new Claude Code session and verify one simple and one complex task.

Use `CLAUDE.example.md` as the copy-ready integration pattern. Claude Code
allows relative and absolute imports; relative paths resolve from the
importing `CLAUDE.md`.

For VSCode extension usage, do not depend on launching the CLI with
`claude --add-dir`. Prefer a policy already inside the opened project tree. If
the extension cannot read the shared source, copy the current policy to:

```text
.claude/policies/model-routing-policy.md
```

Then import it from the project:

```text
@.claude/policies/model-routing-policy.md
```

That copy becomes project-owned and should be refreshed deliberately when the
shared policy changes.

## Adding a Third Model

Extend the policy deliberately rather than inserting another unordered list.

1. Give the model a stable routing role, such as `default`, `upgrade`, or
   `specialist`.
2. Define its exact alias and availability assumptions.
3. State the task signals that select it.
4. Define precedence when more than one model matches.
5. Define fallback behavior when the model is unavailable.
6. Preserve non-blocking recommendation behavior.
7. Update project tests or prompt checks that exercise routing decisions.

For example, a future specialist model might be selected only for security
review. The policy should say whether that specialist outranks Pro, supplements
Pro, or falls back to Pro when unavailable.

## Future Complexity Analysis Skill

A future complexity-analysis Skill may gather evidence and produce a routing
recommendation, but it should not own the routing thresholds.

Recommended separation:

```text
task request
-> complexity-analysis Skill evaluates scope, coupling, risk, and context
-> Model Routing Policy maps those signals to a model recommendation
-> agent reports the recommendation without claiming a switch
-> task execution continues normally
```

The Skill may return structured signals such as:

- estimated file and component span;
- core-logic involvement;
- rollback difficulty;
- security, stability, and performance impact;
- context size and architectural uncertainty;
- recommended model and explanation.

The Policy remains the authority for interpreting those signals. Neither layer
should edit LiteLLM, `settings.json`, scheduled tasks, or environment
variables. Neither layer can audit or guarantee actual model switching.

## Files

- `model-routing-policy.md`: normative routing and confirmation rules.
- `CLAUDE.example.md`: opt-in project import pattern.
- `MODEL_ROUTING_README.md`: design rationale, adoption, and evolution guide.
